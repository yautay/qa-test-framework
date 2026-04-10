pipeline {
  agent none

  options {
    timestamps()
  }

  stages {
    stage('CI') {
      when {
        anyOf {
          branch 'develop'
          branch 'netquarner'
          changeRequest()
        }
      }

      parallel {
        stage('Lint Format Typecheck') {
          agent {
            docker {
              image 'python:3.13-slim'
              reuseNode true
            }
          }
          steps {
            checkout scm
            sh 'python -m pip install --upgrade pip'
            sh 'python -m pip install -e ".[dev]"'
            sh 'python -m ruff check framework tools qa/aso'
            sh 'python -m black --check framework tools qa/aso'
            sh 'python -m mypy framework'
          }
        }

        stage('Security') {
          agent {
            docker {
              image 'python:3.13-slim'
              reuseNode true
            }
          }
          steps {
            checkout scm
            sh 'python -m pip install --upgrade pip'
            sh 'python -m pip install -e ".[dev]"'
            sh 'make security'
          }
        }

        stage('ASO Tests') {
          agent {
            docker {
              image 'python:3.13-slim'
              reuseNode true
            }
          }
          environment {
            HEADLESS = '1'
            IS_GRID_AVAILABLE = '0'
            REPORTING_ENABLED = '0'
            ALLURE_ENABLED = '0'
            PYTEST_HTML_ENABLED = '0'
            RECORD_VIDEO = '0'
          }
          steps {
            checkout scm
            sh 'python -m pip install --upgrade pip'
            sh 'python -m pip install -e ".[dev]"'
            sh 'make verify-discovery'
            sh 'make verify-scenarios'
            sh 'make test-aso'
          }
          post {
            failure {
              archiveArtifacts artifacts: 'artifacts/**', allowEmptyArchive: true
            }
          }
        }

        stage('Frontend UI') {
          agent {
            docker {
              image 'node:22-slim'
              reuseNode true
            }
          }
          steps {
            checkout scm
            dir('framework/visual/ui') {
              sh 'npm ci'
              sh 'npm run test:unit'
              sh 'npm run build:fast'
            }
          }
        }
      }
    }
  }
}
