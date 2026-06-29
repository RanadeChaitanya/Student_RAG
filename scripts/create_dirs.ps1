$dirs = @(
    'backend\api',
    'backend\services',
    'backend\middleware',
    'student_model\mastery',
    'student_model\profile',
    'student_model\session_memory',
    'student_model\long_term_memory',
    'assessment\engine',
    'assessment\evaluator',
    'assessment\tagger',
    'question_bank\app_questions',
    'question_bank\test_questions',
    'question_bank\metadata',
    'question_bank\ingestion',
    'diagnosis\classifier',
    'diagnosis\error_types',
    'diagnosis\concept_tagger',
    'retrieval\orchestrator',
    'retrieval\semantic',
    'retrieval\metadata_filter',
    'retrieval\concept_expansion',
    'retrieval\student_filter',
    'retrieval\reranker',
    'retrieval\context_builder',
    'llm\client',
    'llm\prompts',
    'llm\output_parser',
    'llm\practice_generator',
    'graph\schema',
    'graph\traversal',
    'graph\ingestion',
    'embeddings\generator',
    'embeddings\storage',
    'embeddings\indexer',
    'memory\session_store',
    'memory\history_store',
    'analytics\mastery_trends',
    'analytics\mistake_patterns',
    'analytics\session_reports',
    'tests\unit',
    'tests\integration',
    'tests\performance',
    'tests\e2e',
    'tests\fixtures',
    'configs\development',
    'configs\testing',
    'configs\production',
    'scripts\db',
    'scripts\ingestion',
    'scripts\maintenance',
    'docs\adr',
    'docs\diagrams',
    'docker',
    'deployment\k8s',
    'deployment\env_templates',
    'data'
)

$base = 'D:\JEE\p1'
foreach ($d in $dirs) {
    $path = Join-Path $base $d
    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
        Write-Host "Created: $path"
    }
}
Write-Host "--- All directories created ---"
