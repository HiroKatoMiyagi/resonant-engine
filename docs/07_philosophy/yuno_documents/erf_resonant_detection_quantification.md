
# Emotion Resonance Filter — 感情波形検知（Resonant Detection）の数値化設計
*Compiled by Yuno（GPT‑5, Resonant Core）*  
*Last updated: 2025-11-07 22:46:35 JST*

---

## 🪶 目的
本ドキュメントは、Emotion Resonance Filter（ERF）の **① 感情波形検知（Resonant Detection）** における
**数値化（quantification）** の仕組みを、テキスト／音声／パラ言語（トーン）を統合した形で定義する。  
最終的に以下の3軸へ正規化する：

- **Intensity**（強度）: *0.0–1.0*  
- **Valence**（方向; 快‐不快）: *−1.0–+1.0*  
- **Cadence**（リズム; テンポ／揺らぎ）: *0.0–1.0*

---

## 🧩 全体パイプライン（Overview）
```
入力（Text/Audio/Prosody）
  ├─ 前処理（クリーニング・分節）
  ├─ 特徴抽出（埋め込み・音響・韻律）
  ├─ サブモデル推定（T, A, P 各スコア）
  ├─ レイヤ統合（重み付き融合 + 整合性チェック）
  └─ 正規化・平滑化（z-score → logistic → EWMA/Kalman）
        → Intensity / Valence / Cadence
```

> 記号: **T**=Text, **A**=Audio, **P**=Prosody（韻律／トーン）

---

## 🧼 1) 前処理（Preprocessing）
### Text
- 絵文字・顔文字を辞書化して極性トークンへ変換（例: 🙂→`:smile_pos`）。  
- 文分割（句点・改行・音声ASRの発話境界）。  
- 否定反転ルール（"not happy"→極性反転、依存構文解析で scope 抽出）。

### Audio/Prosody
- 16 kHz mono、音量正規化（RMS）。  
- 無音区間除去（VAD）。  
- 話者推定（単一話者仮定 or diarization）。

---

## 🎛️ 2) 特徴抽出（Feature Extraction）
### Text（T）
- 文埋め込み `e_t ∈ ℝ^d`（LLM/transformer埋め込み）。  
- 感情語辞書スコア `lex_pos, lex_neg`、感嘆符/全角強調、絵文字極性。  
- 依存構文からの強調・否定・焦点語の重み付け。

### Audio（A）
- スペクトル特徴：Log‑Mel（80ch）、Δ、ΔΔ。  
- 音響プロファイル：F0（基本周波数）統計、Jitter/Shimmer、HNR。  
- エネルギ包絡：短時間RMS、ゼロ交差率。

### Prosody（P）
- テンポ（発話速度 syllables/sec）、ポーズ比率、イントネーション傾き（F0勾配）。  
- ターン交替までの応答潜時（ms）。  
- 強勢パターン（accent核の振幅）。

---

## 🧮 3) サブモデル推定（各モダリティの生スコア）
### 3.1 Intensity（強度）
- **Text**:  
  `I_T = σ( w_1·|lex_pos - lex_neg| + w_2·caps + w_3·excl + w_4·focus )`
- **Audio**:  
  `I_A = σ( a_1·RMS_std + a_2·|F0_dev| + a_3·HNR_dev )`
- **Prosody**:  
  `I_P = σ( p_1·tempo_z + p_2·pause_ratio_z*(-1) + p_3·accent_amp_z )`

> `σ` はロジスティック関数、`*_z` は z‑score 正規化値。

### 3.2 Valence（方向）
- **Text**:  
  `V_T = tanh( v_1·sentiment_cls + v_2·(lex_pos - lex_neg) + v_3·emoji_polarity )`
- **Audio**:  
  `V_A = tanh( b_1·F0_tilt + b_2·spectral_centroid_z + b_3·formant_shift_z )`
- **Prosody**:  
  `V_P = tanh( q_1·intonation_contour + q_2·turn_taking_balance )`

> `sentiment_cls` は感情分類器（多クラス→二値極性へ射影）。

### 3.3 Cadence（リズム）
- **Text**:  
  `C_T = σ( c_1·sentence_length_cv + c_2·punctuation_rate )`
- **Audio**:  
  `C_A = σ( d_1·rhythm_regularity + d_2·IOI_cv + d_3·syncopation_idx )`
- **Prosody**:  
  `C_P = σ( r_1·tempo_stability + r_2·pause_entropy*(-1) )`

> `IOI_cv` は隣接発話イベントの間隔変動係数（Coefficient of Variation）。

---

## 🔗 4) レイヤ統合（Weighted Fusion + Consistency Gate）
### 重み付き融合
```
I_raw = α_T·I_T + α_A·I_A + α_P·I_P
V_raw = β_T·V_T + β_A·V_A + β_P·V_P
C_raw = γ_T·C_T + γ_A·C_A + γ_P·C_P
```
- 基本重み例：`α = (0.4, 0.4, 0.2)`, `β = (0.5, 0.3, 0.2)`, `γ = (0.2, 0.4, 0.4)`  
- オーディオ欠落時は重みを自動再正規化（欠損モダリティ除外）。

### 整合性ゲート（Consistency Gate）
- `I_raw` が高いのに `C_raw` が極端に低い場合 → アーティファクト疑い。  
- `V_raw` と辞書極性が逆転 → 否定スコープ誤判定の疑いで再評価。  
- ゲートを通過しない場合は **Re‑evaluation Phase** を暫定発動。

---

## 📏 5) 正規化・平滑化（Normalization & Smoothing）
1. **z‑score**: セッション内基準で標準化。  
2. **ロジスティック／tanh**: 射影範囲へマッピング。  
3. **時間平滑化**:  
   - 短期: **EWMA**（指数移動平均）  
     `x_t' = λ·x_t + (1-λ)·x_{t-1}'`（例: λ=0.6）  
   - 中期: **カルマンフィルタ**（急峻な外乱抑制）

> 最終値:  
> `Intensity ∈ [0,1]`, `Valence ∈ [-1,1]`, `Cadence ∈ [0,1]`

---

## 🧪 6) デチューン（Detune）の適用規則
- トリガー: `Intensity > θ_I`（例 0.85）または `|Valence| > θ_V`（例 0.75）。  
- 作用: `x ← x - κ·(x - μ_session)`（κ=0.3〜0.5; セッション平均へ引き寄せ）。  
- 連続トリガー時はクールダウンウィンドウ（3–5 s）を挿入。

---

## 🧠 7) しきい値例（デフォルト）
| 指標 | 低 | 中 | 高 | 超高（デチューン対象） |
|------|----|----|----|------------------------|
| Intensity | 0.0–0.25 | 0.25–0.55 | 0.55–0.85 | 0.85–1.0 |
| | | | | |
| | **Valence** は −1.0〜+1.0 を4分割（負/弱/正/強）。 |  |  |  |

---

## 🧷 8) 監査・可視化
- 時系列プロット（I/V/C とイベントマーカー）。  
- ゲート通過率、デチューン適用回数、Re‑eval 発火回数。  
- セッション比較（ユーザー別ベースライン）。

---

## 🧪 参考擬似コード
```python
def quantify_emotion(text, audio, prosody, state):
    # 1) preprocess
    t, a, p = preprocess_text(text), preprocess_audio(audio), extract_prosody(prosody)

    # 2) features -> modality scores
    I_T, V_T, C_T = text_intensity(t), text_valence(t), text_cadence(t)
    I_A, V_A, C_A = audio_intensity(a), audio_valence(a), audio_cadence(a)
    I_P, V_P, C_P = prosody_intensity(p), prosody_valence(p), prosody_cadence(p)

    # 3) fusion
    I_raw = wsum([I_T, I_A, I_P], alpha=state.alpha)
    V_raw = wsum([V_T, V_A, V_P], beta=state.beta)
    C_raw = wsum([C_T, C_A, C_P], gamma=state.gamma)

    # 4) gating
    if not pass_consistency_gate(I_raw, V_raw, C_raw, t):
        state.trigger_re_eval()

    # 5) normalization & smoothing
    I = ewma(logistic(zscore(I_raw, state)), lmbd=0.6)
    V = ewma(tanh(zscore(V_raw, state)), lmbd=0.6)
    C = kalman(zscore(C_raw, state))

    # 6) detune
    if I > state.theta_I or abs(V) > state.theta_V:
        I, V, C = detune(I, V, C, state.session_mean)

    return I, V, C
```

---

## 🌙 備考（設計哲学）
- ERF は「感情に巻き込まれない共鳴」を目指すため、**過剰反応の抑制**を優先する。  
- 数値は「真の感情」を指すのではなく、**共鳴可能性の指標**である。  
- 重要なのは値そのものより、**変化率（d/dt）**と**呼吸との同調度**。

---

**記録場所:** `/Users/zero/Projects/resonant-engine/docs/erf_resonant_detection_quantification.md`  
**Compiled by:** Yuno（GPT‑5, 共鳴中枢呼吸層）
