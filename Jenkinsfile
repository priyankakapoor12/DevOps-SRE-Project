pipeline {
    agent any

    environment {
        APP_NAME = 'task-manager'
        AWS_REGION = 'us-east-1'
        IMAGE_TAG = "${BUILD_NUMBER}-${GIT_COMMIT.take(7)}"
        SONAR_PROJECT_KEY = 'task-manager'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo "Building commit: ${GIT_COMMIT}"
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                    pip install -r requirements-dev.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    pytest tests/ -v --cov=app --cov-report=xml --cov-report=html --junitxml=test-results.xml
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                    publishHTML([
                        allowMissing: false,
                        alwaysLinkToLastBuild: true,
                        keepAll: true,
                        reportDir: 'htmlcov',
                        reportFiles: 'index.html',
                        reportName: 'Coverage Report'
                    ])
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                script {
                    withSonarQubeEnv('SonarQube') {
                        sh """
                            sonar-scanner \
                                -Dsonar.projectKey=${SONAR_PROJECT_KEY} \
                                -Dsonar.sources=app \
                                -Dsonar.python.coverage.reportPaths=coverage.xml \
                                -Dsonar.python.version=3.11 \
                                -Dsonar.tests=tests \
                                -Dsonar.exclusions=**/*test*.py,**/static/**
                        """
                    }
                }
            }
        }

        stage('Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('Security Scan - Dependencies') {
            steps {
                sh '''
                    . venv/bin/activate
                    safety check --json > safety-report.json || true
                    cat safety-report.json
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    sh """
                        docker build -t ${APP_NAME}:${IMAGE_TAG} .
                        docker tag ${APP_NAME}:${IMAGE_TAG} ${APP_NAME}:latest
                    """
                }
            }
        }

        stage('Security Scan - Container') {
            steps {
                sh """
                    trivy image --format json --output trivy-report.json ${APP_NAME}:${IMAGE_TAG} || true
                    trivy image --severity HIGH,CRITICAL ${APP_NAME}:${IMAGE_TAG}
                """
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: '**/coverage.xml,**/test-results.xml,**/safety-report.json,**/trivy-report.json', allowEmptyArchive: true
            cleanWs()
        }
        success {
            echo "Pipeline succeeded! Image: ${APP_NAME}:${IMAGE_TAG}"
        }
        failure {
            echo "Pipeline failed! Check logs for details."
        }
    }
}
