import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import './App.css'

const API_BASE = 'http://localhost:8000'
const WS_URL = 'ws://localhost:8000/ws'

function App() {
  const [messages, setMessages] = useState([])
  const [specs, setSpecs] = useState([])
  const [intents, setIntents] = useState([])
  const [stats, setStats] = useState(null)
  const [newMessage, setNewMessage] = useState('')
  const [activeTab, setActiveTab] = useState('messages') // messages, specs, intents
  const [wsConnected, setWsConnected] = useState(false)
  const wsRef = useRef(null)

  // WebSocket接続
  useEffect(() => {
    const connectWebSocket = () => {
      const ws = new WebSocket(WS_URL)
      
      ws.onopen = () => {
        console.log('✅ WebSocket接続成功')
        setWsConnected(true)
      }
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        console.log('📨 WebSocket受信:', data)
        
        // テーブル変更通知を受けたらデータを再取得
        if (data.payload && data.payload.table) {
          loadData()
        }
      }
      
      ws.onerror = (error) => {
        console.error('❌ WebSocketエラー:', error)
        setWsConnected(false)
      }
      
      ws.onclose = () => {
        console.log('🔌 WebSocket切断 - 5秒後に再接続')
        setWsConnected(false)
        setTimeout(connectWebSocket, 5000) // 5秒後に再接続
      }
      
      wsRef.current = ws
    }
    
    connectWebSocket()
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  // 初回データ取得
  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [messagesRes, specsRes, intentsRes, statsRes] = await Promise.all([
        axios.get(`${API_BASE}/api/messages?limit=20`),
        axios.get(`${API_BASE}/api/specs?limit=20`),
        axios.get(`${API_BASE}/api/intents?limit=20`),
        axios.get(`${API_BASE}/api/stats`)
      ])
      setMessages(messagesRes.data)
      setSpecs(specsRes.data)
      setIntents(intentsRes.data)
      setStats(statsRes.data)
    } catch (error) {
      console.error('データ取得エラー:', error)
    }
  }

  const sendMessage = async () => {
    if (!newMessage.trim()) return
    
    try {
      await axios.post(`${API_BASE}/api/messages`, {
        content: newMessage,
        sender: 'user'
      })
      setNewMessage('')
      loadData()
    } catch (error) {
      console.error('メッセージ送信エラー:', error)
    }
  }

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-yellow-500',
      processing: 'bg-blue-500',
      completed: 'bg-green-500',
      error: 'bg-red-500'
    }
    return colors[status] || 'bg-gray-500'
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* ヘッダー */}
      <header className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">🌿 Resonant Engine</h1>
          {stats && (
            <div className="flex gap-4 text-sm items-center">
              <span>メッセージ: {stats.messages}</span>
              <span>仕様書: {stats.specs}</span>
              <span>Intent: {stats.intents}</span>
              <span className={`px-2 py-1 rounded text-xs ${wsConnected ? 'bg-green-600' : 'bg-red-600'}`}>
                {wsConnected ? '🟢 リアルタイム' : '🔴 切断'}
              </span>
            </div>
          )}
        </div>
      </header>

      {/* メインコンテンツ */}
      <div className="container mx-auto p-4">
        {/* タブ */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={() => setActiveTab('messages')}
            className={`px-4 py-2 rounded ${activeTab === 'messages' ? 'bg-blue-600' : 'bg-gray-700'}`}
          >
            メッセージ
          </button>
          <button
            onClick={() => setActiveTab('specs')}
            className={`px-4 py-2 rounded ${activeTab === 'specs' ? 'bg-blue-600' : 'bg-gray-700'}`}
          >
            仕様書
          </button>
          <button
            onClick={() => setActiveTab('intents')}
            className={`px-4 py-2 rounded ${activeTab === 'intents' ? 'bg-blue-600' : 'bg-gray-700'}`}
          >
            Intent
          </button>
        </div>

        {/* メッセージタブ */}
        {activeTab === 'messages' && (
          <div>
            <div className="bg-gray-800 rounded-lg p-4 mb-4 h-96 overflow-y-auto">
              {messages.length === 0 ? (
                <p className="text-gray-400 text-center py-8">メッセージがありません</p>
              ) : (
                <div className="space-y-2">
                  {messages.map((msg) => {
                    // メッセージから生成されたIntentを検索
                    const linkedIntent = msg.intent_id 
                      ? intents.find(intent => intent.id === msg.intent_id)
                      : null
                    
                    return (
                      <div key={msg.id} className="bg-gray-700 p-3 rounded hover:bg-gray-650 transition">
                        <div className="flex justify-between items-start mb-1">
                          <span className="font-bold text-blue-400">{msg.sender}</span>
                          <span className="text-xs text-gray-400">
                            {new Date(msg.created_at).toLocaleString('ja-JP')}
                          </span>
                        </div>
                        <p className="text-gray-200 mb-2">{msg.content}</p>
                        
                        {/* Intent紐付け表示 */}
                        {linkedIntent && (
                          <div className="flex items-center gap-2 mt-2 pt-2 border-t border-gray-600">
                            <span className="text-xs text-gray-400">🔗 Intent:</span>
                            <button
                              onClick={() => setActiveTab('intents')}
                              className="text-xs bg-purple-600 hover:bg-purple-700 px-2 py-1 rounded transition flex items-center gap-1"
                            >
                              <span>⚡</span>
                              <span>{linkedIntent.type}</span>
                              <span className={`inline-block w-2 h-2 rounded-full ${getStatusColor(linkedIntent.status)}`}></span>
                            </button>
                            <span className="text-xs text-gray-500">
                              ID: {linkedIntent.id.substring(0, 8)}...
                            </span>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>

            {/* メッセージ入力 */}
            <div className="flex gap-2">
              <input
                type="text"
                value={newMessage}
                onChange={(e) => setNewMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                placeholder="メッセージを入力..."
                className="flex-1 bg-gray-800 border border-gray-700 rounded px-4 py-2 focus:outline-none focus:border-blue-500"
              />
              <button
                onClick={sendMessage}
                className="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded font-medium"
              >
                送信
              </button>
            </div>
          </div>
        )}

        {/* 仕様書タブ */}
        {activeTab === 'specs' && (
          <div className="bg-gray-800 rounded-lg p-4">
            {specs.length === 0 ? (
              <p className="text-gray-400 text-center py-8">仕様書がありません</p>
            ) : (
              <div className="space-y-3">
                {specs.map((spec) => (
                  <div key={spec.id} className="bg-gray-700 p-4 rounded hover:bg-gray-600 cursor-pointer">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-bold text-lg">{spec.title}</h3>
                      <span className="text-xs bg-blue-600 px-2 py-1 rounded">{spec.status}</span>
                    </div>
                    <p className="text-gray-300 text-sm line-clamp-2">{spec.content}</p>
                    <div className="text-xs text-gray-400 mt-2">
                      更新: {new Date(spec.updated_at).toLocaleString('ja-JP')}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Intentタブ */}
        {activeTab === 'intents' && (
          <div className="bg-gray-800 rounded-lg p-4">
            {intents.length === 0 ? (
              <p className="text-gray-400 text-center py-8">Intentがありません</p>
            ) : (
              <div className="space-y-3">
                {intents.map((intent) => (
                  <div key={intent.id} className="bg-gray-700 p-4 rounded hover:bg-gray-650 transition">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-lg">⚡ {intent.type}</span>
                        <span className="text-xs text-gray-400">
                          {intent.id.substring(0, 8)}...
                        </span>
                        {/* 自動生成バッジ */}
                        {intent.source === 'auto_generated' && (
                          <span className="text-xs bg-gradient-to-r from-purple-600 to-pink-600 px-2 py-1 rounded font-semibold">
                            ✨ 自動生成
                          </span>
                        )}
                      </div>
                      <span className={`text-xs px-2 py-1 rounded ${getStatusColor(intent.status)}`}>
                        {intent.status}
                      </span>
                    </div>
                    
                    {/* リンクされたMessage表示 */}
                    {intent.linked_message && (
                      <div className="bg-gray-800 p-3 rounded mb-3 border-l-4 border-blue-500">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs text-gray-400">🔗 元メッセージ:</span>
                          <span className="text-xs font-bold text-blue-400">
                            {intent.linked_message.sender}
                          </span>
                          <span className="text-xs text-gray-500">
                            {new Date(intent.linked_message.created_at).toLocaleString('ja-JP')}
                          </span>
                        </div>
                        <p className="text-sm text-gray-300 line-clamp-2">
                          "{intent.linked_message.content}"
                        </p>
                        <button
                          onClick={() => setActiveTab('messages')}
                          className="text-xs text-blue-400 hover:text-blue-300 mt-1 transition"
                        >
                          → メッセージを表示
                        </button>
                      </div>
                    )}
                    
                    {/* Intent data */}
                    {intent.data && (
                      <div className="bg-gray-800 p-3 rounded mb-2">
                        <div className="text-xs text-gray-400 mb-1">詳細データ:</div>
                        <div className="text-sm space-y-1">
                          {intent.data.target && (
                            <div>
                              <span className="text-gray-400">対象: </span>
                              <span className="text-gray-200">{intent.data.target}</span>
                            </div>
                          )}
                          {intent.data.confidence && (
                            <div>
                              <span className="text-gray-400">確信度: </span>
                              <span className={`font-semibold ${
                                intent.data.confidence === 'high' ? 'text-green-400' :
                                intent.data.confidence === 'medium' ? 'text-yellow-400' :
                                'text-orange-400'
                              }`}>
                                {intent.data.confidence}
                              </span>
                            </div>
                          )}
                          {intent.data.description && (
                            <div>
                              <span className="text-gray-400">説明: </span>
                              <span className="text-gray-200">{intent.data.description}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                    
                    <div className="text-xs text-gray-400">
                      作成: {new Date(intent.created_at).toLocaleString('ja-JP')}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default App

