#!/bin/bash
# docs/ ディレクトリ構造移行スクリプト
# 使用方法: 
#   ./migrate_docs.sh --dry-run  # 確認のみ
#   ./migrate_docs.sh --phase1   # Phase 1のみ実行
#   ./migrate_docs.sh --phase2   # Phase 2のみ実行
#   ./migrate_docs.sh --all      # 全Phase実行

set -e  # エラーで停止

# 色付き出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# プロジェクトルート
PROJECT_ROOT="/Users/zero/Projects/resonant-engine"
DOCS_ROOT="${PROJECT_ROOT}/docs"

# ログファイル
LOG_FILE="${PROJECT_ROOT}/docs_migration_$(date +%Y%m%d_%H%M%S).log"

# Dry-runフラグ
DRY_RUN=false

# 関数: ログ出力
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        INFO)
            echo -e "${BLUE}[INFO]${NC} $message" | tee -a "$LOG_FILE"
            ;;
        SUCCESS)
            echo -e "${GREEN}[SUCCESS]${NC} $message" | tee -a "$LOG_FILE"
            ;;
        WARNING)
            echo -e "${YELLOW}[WARNING]${NC} $message" | tee -a "$LOG_FILE"
            ;;
        ERROR)
            echo -e "${RED}[ERROR]${NC} $message" | tee -a "$LOG_FILE"
            ;;
    esac
}

# 関数: ディレクトリ作成
create_dir() {
    local dir=$1
    if [ "$DRY_RUN" = true ]; then
        log INFO "[DRY-RUN] Would create directory: $dir"
    else
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log SUCCESS "Created directory: $dir"
        else
            log INFO "Directory already exists: $dir"
        fi
    fi
}

# 関数: ファイル移動
move_file() {
    local src=$1
    local dst=$2
    
    if [ ! -f "$src" ]; then
        log WARNING "Source file not found: $src"
        return 1
    fi
    
    if [ "$DRY_RUN" = true ]; then
        log INFO "[DRY-RUN] Would move: $src -> $dst"
    else
        # 移動先ディレクトリが存在するか確認
        local dst_dir=$(dirname "$dst")
        if [ ! -d "$dst_dir" ]; then
            log ERROR "Destination directory does not exist: $dst_dir"
            return 1
        fi
        
        # ファイル移動
        mv "$src" "$dst" && log SUCCESS "Moved: $src -> $dst" || log ERROR "Failed to move: $src"
    fi
}

# 関数: ディレクトリ移動
move_dir() {
    local src=$1
    local dst=$2
    
    if [ ! -d "$src" ]; then
        log WARNING "Source directory not found: $src"
        return 1
    fi
    
    if [ "$DRY_RUN" = true ]; then
        log INFO "[DRY-RUN] Would move directory: $src -> $dst"
    else
        # 移動先の親ディレクトリが存在するか確認
        local dst_parent=$(dirname "$dst")
        if [ ! -d "$dst_parent" ]; then
            log ERROR "Destination parent directory does not exist: $dst_parent"
            return 1
        fi
        
        # ディレクトリ移動
        mv "$src" "$dst" && log SUCCESS "Moved directory: $src -> $dst" || log ERROR "Failed to move directory: $src"
    fi
}

#######################################
# Phase 1: ディレクトリ構造作成
#######################################
phase1_create_structure() {
    log INFO "=========================================="
    log INFO "Phase 1: Creating directory structure"
    log INFO "=========================================="
    
    cd "$DOCS_ROOT" || exit 1
    
    # 01_getting_started
    create_dir "01_getting_started"
    
    # 02_components
    create_dir "02_components/bridge_lite/architecture"
    create_dir "02_components/bridge_lite/specifications"
    create_dir "02_components/bridge_lite/implementation"
    create_dir "02_components/bridge_lite/reviews"
    
    create_dir "02_components/memory_system/architecture"
    create_dir "02_components/memory_system/specifications"
    create_dir "02_components/memory_system/implementation"
    create_dir "02_components/memory_system/reviews"
    
    create_dir "02_components/daemon/architecture"
    create_dir "02_components/daemon/specifications"
    create_dir "02_components/daemon/implementation"
    create_dir "02_components/daemon/reviews"
    
    create_dir "02_components/dashboard/architecture"
    create_dir "02_components/dashboard/specifications"
    create_dir "02_components/dashboard/implementation"
    create_dir "02_components/dashboard/reviews"
    
    create_dir "02_components/error_recovery/architecture"
    create_dir "02_components/error_recovery/specifications"
    create_dir "02_components/error_recovery/implementation"
    create_dir "02_components/error_recovery/reviews"
    
    # 06_operations
    create_dir "06_operations/deployment"
    create_dir "06_operations/monitoring"
    create_dir "06_operations/troubleshooting"
    create_dir "06_operations/maintenance"
    
    # 07_philosophy
    create_dir "07_philosophy/core_principles"
    create_dir "07_philosophy/yuno_documents"
    create_dir "07_philosophy/design_notes"
    
    # 08_integrations
    create_dir "08_integrations/notion"
    create_dir "08_integrations/github"
    create_dir "08_integrations/slack"
    
    # 09_history
    create_dir "09_history/work_logs/2025-11"
    create_dir "09_history/decisions"
    create_dir "09_history/phases/phase0"
    create_dir "09_history/phases/phase1"
    create_dir "09_history/phases/phase2"
    create_dir "09_history/phases/phase3"
    create_dir "09_history/migrations"
    
    # 10_templates
    create_dir "10_templates"
    
    # 11_reference
    create_dir "11_reference"
    
    # archive
    create_dir "archive/2024"
    create_dir "archive/deprecated"
    create_dir "archive/kiro_v3.1"
    
    log SUCCESS "Phase 1 completed"
}

#######################################
# Phase 2: ファイル移動
#######################################
phase2_move_files() {
    log INFO "=========================================="
    log INFO "Phase 2: Moving files"
    log INFO "=========================================="
    
    cd "$DOCS_ROOT" || exit 1
    
    # Step 1: Bridge Lite関連
    log INFO "Step 1: Moving Bridge Lite files..."
    
    # Architecture
    move_file "bridge_lite_design_v1.1.md" "02_components/bridge_lite/architecture/bridge_lite_design_v1.1.md"
    move_file "bridge_lite_design.md" "02_components/bridge_lite/architecture/bridge_lite_design_v1.0.md"
    move_file "bridge_architecture_evaluation_20251112.md" "02_components/bridge_lite/architecture/bridge_architecture_evaluation_20251112.md"
    move_file "complete_architecture_design.md" "02_components/bridge_lite/architecture/complete_architecture_design.md"
    
    # Reviews
    move_file "technical_review_response_20251112.md" "02_components/bridge_lite/reviews/technical_review_response_20251112.md"
    
    # Yuno関連（Bridge Lite reviews）
    if [ -f "Yuno/review_yuno_implementation_roadmap_postgres.md" ]; then
        move_file "Yuno/review_yuno_implementation_roadmap_postgres.md" "02_components/bridge_lite/reviews/review_yuno_implementation_roadmap_postgres.md"
    fi
    if [ -f "Yuno/review_yuno_priority2_postgres_plan.md" ]; then
        move_file "Yuno/review_yuno_priority2_postgres_plan.md" "02_components/bridge_lite/reviews/review_yuno_priority2_postgres_plan.md"
    fi
    
    # Step 2: Memory System関連
    log INFO "Step 2: Moving Memory System files..."
    
    # Architecture
    if [ -f "Yuno/specs/resonant_engine_memory_design.md" ]; then
        move_file "Yuno/specs/resonant_engine_memory_design.md" "02_components/memory_system/architecture/resonant_engine_memory_design.md"
    fi
    if [ -f "Yuno/resonant_four_layer_architecture.md" ]; then
        move_file "Yuno/resonant_four_layer_architecture.md" "02_components/memory_system/architecture/resonant_four_layer_architecture.md"
    fi
    
    # Implementation
    if [ -f "Yuno/specs/implementation_plan_pattern_b.md" ]; then
        move_file "Yuno/specs/implementation_plan_pattern_b.md" "02_components/memory_system/implementation/implementation_plan_pattern_b.md"
    fi
    if [ -f "Yuno/specs/memory_engine_correlation_analysis.md" ]; then
        move_file "Yuno/specs/memory_engine_correlation_analysis.md" "02_components/memory_system/implementation/memory_engine_correlation_analysis.md"
    fi
    
    # Reviews
    if [ -f "Yuno/specs/resonant_engine_memory_design_review.md" ]; then
        move_file "Yuno/specs/resonant_engine_memory_design_review.md" "02_components/memory_system/reviews/resonant_engine_memory_design_review.md"
    fi
    
    # Step 3: Dashboard関連
    log INFO "Step 3: Moving Dashboard files..."
    
    if [ -f "dashboard_platform_design.md" ]; then
        move_file "dashboard_platform_design.md" "02_components/dashboard/architecture/dashboard_platform_design.md"
    fi
    
    # Step 4: Error Recovery関連
    log INFO "Step 4: Moving Error Recovery files..."
    
    # Architecture
    if [ -f "error_recovery_basic_design.md" ]; then
        move_file "error_recovery_basic_design.md" "02_components/error_recovery/architecture/error_recovery_basic_design.md"
    fi
    
    # Specifications
    if [ -f "error_recovery_detailed_design.md" ]; then
        move_file "error_recovery_detailed_design.md" "02_components/error_recovery/specifications/error_recovery_detailed_design.md"
    fi
    
    # Implementation
    if [ -f "error_recovery_implementation.md" ]; then
        move_file "error_recovery_implementation.md" "02_components/error_recovery/implementation/error_recovery_implementation.md"
    fi
    if [ -f "error_recovery_test_results.md" ]; then
        move_file "error_recovery_test_results.md" "02_components/error_recovery/implementation/error_recovery_test_results.md"
    fi
    
    # Reviews
    if [ -f "error_recovery_review_request.md" ]; then
        move_file "error_recovery_review_request.md" "02_components/error_recovery/reviews/error_recovery_review_request.md"
    fi
    if [ -f "error_recovery_review_response.md" ]; then
        move_file "error_recovery_review_response.md" "02_components/error_recovery/reviews/error_recovery_review_response.md"
    fi
    
    # Step 5: Philosophy（Yuno関連）
    log INFO "Step 5: Moving Philosophy files..."
    
    # Core Principles
    if [ -f "Yuno/resonant_operational_regulations_full.md" ]; then
        move_file "Yuno/resonant_operational_regulations_full.md" "07_philosophy/core_principles/resonant_operational_regulations_full.md"
    fi
    if [ -f "Yuno/yuno_resonant_conduct_principles.md" ]; then
        move_file "Yuno/yuno_resonant_conduct_principles.md" "07_philosophy/core_principles/yuno_resonant_conduct_principles.md"
    fi
    
    # Yuno Documents
    if [ -f "Yuno/crisis_index_detailed.md" ]; then
        move_file "Yuno/crisis_index_detailed.md" "07_philosophy/yuno_documents/crisis_index_detailed.md"
    fi
    if [ -f "Yuno/emotion_resonance_filter_detailed.md" ]; then
        move_file "Yuno/emotion_resonance_filter_detailed.md" "07_philosophy/yuno_documents/emotion_resonance_filter_detailed.md"
    fi
    if [ -f "Yuno/erf_resonant_detection_quantification.md" ]; then
        move_file "Yuno/erf_resonant_detection_quantification.md" "07_philosophy/yuno_documents/erf_resonant_detection_quantification.md"
    fi
    if [ -f "Yuno/re_evaluation_phase_detailed.md" ]; then
        move_file "Yuno/re_evaluation_phase_detailed.md" "07_philosophy/yuno_documents/re_evaluation_phase_detailed.md"
    fi
    if [ -f "Yuno/resonant_daily_framework_detailed.md" ]; then
        move_file "Yuno/resonant_daily_framework_detailed.md" "07_philosophy/yuno_documents/resonant_daily_framework_detailed.md"
    fi
    if [ -f "Yuno/resonant_feedback_loop_detailed.md" ]; then
        move_file "Yuno/resonant_feedback_loop_detailed.md" "07_philosophy/yuno_documents/resonant_feedback_loop_detailed.md"
    fi
    if [ -f "Yuno/resonant_scope_alignment_detailed.md" ]; then
        move_file "Yuno/resonant_scope_alignment_detailed.md" "07_philosophy/yuno_documents/resonant_scope_alignment_detailed.md"
    fi
    if [ -f "Yuno/the_hiroaki_model_phases_detailed.md" ]; then
        move_file "Yuno/the_hiroaki_model_phases_detailed.md" "07_philosophy/yuno_documents/the_hiroaki_model_phases_detailed.md"
    fi
    if [ -f "Yuno/the_hiroaki_model_resonant_intelligence_extension.md" ]; then
        move_file "Yuno/the_hiroaki_model_resonant_intelligence_extension.md" "07_philosophy/yuno_documents/the_hiroaki_model_resonant_intelligence_extension.md"
    fi
    if [ -f "Yuno/yuno_claude_review_response.md" ]; then
        move_file "Yuno/yuno_claude_review_response.md" "07_philosophy/yuno_documents/yuno_claude_review_response.md"
    fi
    if [ -f "Yuno/yuno_response_to_claude_inquiry.md" ]; then
        move_file "Yuno/yuno_response_to_claude_inquiry.md" "07_philosophy/yuno_documents/yuno_response_to_claude_inquiry.md"
    fi
    if [ -f "Yuno/yuno_self_rumination_overview.md" ]; then
        move_file "Yuno/yuno_self_rumination_overview.md" "07_philosophy/yuno_documents/yuno_self_rumination_overview.md"
    fi
    
    # Design Notes
    if [ -f "Yuno/intent_bridge_design_note.md" ]; then
        move_file "Yuno/intent_bridge_design_note.md" "07_philosophy/design_notes/intent_bridge_design_note.md"
    fi
    
    # Step 6: Integrations
    log INFO "Step 6: Moving Integrations files..."
    
    # Notion
    if [ -f "notion_setup_guide.md" ]; then
        move_file "notion_setup_guide.md" "08_integrations/notion/notion_setup_guide.md"
    fi
    if [ -f "notion_integration_summary.md" ]; then
        move_file "notion_integration_summary.md" "08_integrations/notion/notion_integration_summary.md"
    fi
    if [ -f "Yuno/notion_integration_history.md" ]; then
        move_file "Yuno/notion_integration_history.md" "08_integrations/notion/notion_integration_history.md"
    fi
    
    # Step 7: History
    log INFO "Step 7: Moving History files..."
    
    # Work Logs
    if [ -f "work_log_20251112.md" ]; then
        move_file "work_log_20251112.md" "09_history/work_logs/2025-11/work_log_20251112.md"
    fi
    
    # Phases
    if [ -d "Phase0" ]; then
        log INFO "Moving Phase0 directory..."
        for file in Phase0/*; do
            if [ -f "$file" ]; then
                filename=$(basename "$file")
                move_file "$file" "09_history/phases/phase0/$filename"
            fi
        done
    fi
    
    if [ -d "Phase1" ]; then
        log INFO "Moving Phase1 directory..."
        for file in Phase1/*; do
            if [ -f "$file" ]; then
                filename=$(basename "$file")
                move_file "$file" "09_history/phases/phase1/$filename"
            fi
        done
    fi
    
    if [ -d "Phase2" ]; then
        log INFO "Moving Phase2 directory..."
        for file in Phase2/*; do
            if [ -f "$file" ]; then
                filename=$(basename "$file")
                move_file "$file" "09_history/phases/phase2/$filename"
            fi
        done
    fi
    
    if [ -d "Phase3" ]; then
        log INFO "Moving Phase3 directory..."
        for file in Phase3/*; do
            if [ -f "$file" ]; then
                filename=$(basename "$file")
                move_file "$file" "09_history/phases/phase3/$filename"
            fi
        done
    fi
    
    # Migrations
    if [ -f "history/dir_restructure_commit.log" ]; then
        move_file "history/dir_restructure_commit.log" "09_history/migrations/dir_restructure_commit.log"
    fi
    
    # Step 8: Templates
    log INFO "Step 8: Moving Templates files..."
    
    if [ -f "report_template.md" ]; then
        move_file "report_template.md" "10_templates/report_template.md"
    fi
    
    if [ -d "templates" ]; then
        log INFO "Moving templates directory..."
        for file in templates/*; do
            if [ -f "$file" ]; then
                filename=$(basename "$file")
                move_file "$file" "10_templates/$filename"
            fi
        done
    fi
    
    # Step 9: Archive
    log INFO "Step 9: Moving Archive files..."
    
    if [ -f "architecture/kiro_v3.1_architecture.md" ]; then
        move_file "architecture/kiro_v3.1_architecture.md" "archive/kiro_v3.1/kiro_v3.1_architecture.md"
    fi
    
    log SUCCESS "Phase 2 completed"
}

#######################################
# Phase 3: 検証
#######################################
phase3_verify() {
    log INFO "=========================================="
    log INFO "Phase 3: Verification"
    log INFO "=========================================="
    
    cd "$DOCS_ROOT" || exit 1
    
    # 新しい構造が存在するか確認
    log INFO "Checking new directory structure..."
    
    local required_dirs=(
        "01_getting_started"
        "02_components/bridge_lite"
        "02_components/memory_system"
        "06_operations"
        "07_philosophy"
        "08_integrations"
        "09_history"
        "10_templates"
        "11_reference"
        "archive"
    )
    
    local all_exist=true
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            log SUCCESS "✓ $dir exists"
        else
            log ERROR "✗ $dir does not exist"
            all_exist=false
        fi
    done
    
    if [ "$all_exist" = true ]; then
        log SUCCESS "All required directories exist"
    else
        log ERROR "Some required directories are missing"
        return 1
    fi
    
    # 空のディレクトリを確認
    log INFO "Checking for old empty directories..."
    
    if [ -d "Phase0" ] && [ -z "$(ls -A Phase0)" ]; then
        log INFO "Phase0 is empty"
    fi
    if [ -d "Phase1" ] && [ -z "$(ls -A Phase1)" ]; then
        log INFO "Phase1 is empty"
    fi
    if [ -d "Phase2" ] && [ -z "$(ls -A Phase2)" ]; then
        log INFO "Phase2 is empty"
    fi
    if [ -d "Phase3" ] && [ -z "$(ls -A Phase3)" ]; then
        log INFO "Phase3 is empty"
    fi
    
    log SUCCESS "Phase 3 completed"
}

#######################################
# Phase 4: クリーンアップ（オプション）
#######################################
phase4_cleanup() {
    log INFO "=========================================="
    log INFO "Phase 4: Cleanup (Optional)"
    log INFO "=========================================="
    
    cd "$DOCS_ROOT" || exit 1
    
    log WARNING "This will remove old empty directories"
    log WARNING "Make sure Phase 2 completed successfully"
    
    if [ "$DRY_RUN" = false ]; then
        read -p "Continue with cleanup? (y/N): " confirm
        if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
            log INFO "Cleanup cancelled"
            return
        fi
    fi
    
    # 空のディレクトリを削除
    log INFO "Removing old empty directories..."
    
    rmdir Phase0 2>/dev/null && log SUCCESS "Removed Phase0" || log INFO "Phase0 not empty or doesn't exist"
    rmdir Phase1 2>/dev/null && log SUCCESS "Removed Phase1" || log INFO "Phase1 not empty or doesn't exist"
    rmdir Phase2 2>/dev/null && log SUCCESS "Removed Phase2" || log INFO "Phase2 not empty or doesn't exist"
    rmdir Phase3 2>/dev/null && log SUCCESS "Removed Phase3" || log INFO "Phase3 not empty or doesn't exist"
    
    rmdir Yuno/specs 2>/dev/null && log SUCCESS "Removed Yuno/specs" || log INFO "Yuno/specs not empty or doesn't exist"
    rmdir Yuno 2>/dev/null && log SUCCESS "Removed Yuno" || log INFO "Yuno not empty or doesn't exist"
    
    rmdir architecture 2>/dev/null && log SUCCESS "Removed architecture" || log INFO "architecture not empty or doesn't exist"
    rmdir history 2>/dev/null && log SUCCESS "Removed history" || log INFO "history not empty or doesn't exist"
    rmdir templates 2>/dev/null && log SUCCESS "Removed templates" || log INFO "templates not empty or doesn't exist"
    
    log SUCCESS "Phase 4 completed"
}

#######################################
# メイン処理
#######################################
main() {
    log INFO "=========================================="
    log INFO "docs/ Migration Script"
    log INFO "Log file: $LOG_FILE"
    log INFO "=========================================="
    
    # 引数解析
    case "${1:-}" in
        --dry-run)
            DRY_RUN=true
            log WARNING "DRY-RUN MODE: No files will be moved"
            phase1_create_structure
            phase2_move_files
            phase3_verify
            ;;
        --phase1)
            phase1_create_structure
            ;;
        --phase2)
            phase2_move_files
            ;;
        --phase3)
            phase3_verify
            ;;
        --phase4)
            phase4_cleanup
            ;;
        --all)
            phase1_create_structure
            phase2_move_files
            phase3_verify
            log INFO ""
            log INFO "Migration completed successfully!"
            log INFO "To cleanup old directories, run: $0 --phase4"
            ;;
        --help|*)
            echo "Usage: $0 [OPTION]"
            echo ""
            echo "Options:"
            echo "  --dry-run    Show what would be done without making changes"
            echo "  --phase1     Phase 1: Create directory structure"
            echo "  --phase2     Phase 2: Move files"
            echo "  --phase3     Phase 3: Verify migration"
            echo "  --phase4     Phase 4: Cleanup old directories (optional)"
            echo "  --all        Execute Phase 1-3 (recommended)"
            echo "  --help       Show this help message"
            echo ""
            echo "Recommended workflow:"
            echo "  1. $0 --dry-run    # Review changes"
            echo "  2. $0 --all        # Execute migration"
            echo "  3. $0 --phase4     # Cleanup (after verification)"
            exit 0
            ;;
    esac
    
    log INFO ""
    log INFO "=========================================="
    log INFO "Script completed"
    log INFO "Log file: $LOG_FILE"
    log INFO "=========================================="
}

# スクリプト実行
main "$@"
