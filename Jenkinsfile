pipeline {
    agent any

    environment {
        APP_NAME = 'devops-sre-task-manager'
        AWS_REGION = 'us-east-1'
        IMAGE_TAG = "${BUILD_NUMBER}-${GIT_COMMIT.take(7)}"
        SONAR_PROJECT_KEY = 'DevOps-SRE-Project'
        EKS_CLUSTER_NAME = 'devops-sre-cluster'
        K8S_NAMESPACE = 'task-manager'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    echo "Building commit: ${GIT_COMMIT}"

                    // Get AWS Account ID dynamically using IAM instance role
                    env.ECR_REGISTRY = sh(
                        script: 'aws sts get-caller-identity --query Account --output text',
                        returnStdout: true
                    ).trim() + ".dkr.ecr.${AWS_REGION}.amazonaws.com"

                    echo "ECR Registry: ${env.ECR_REGISTRY}"
                }
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

        stage('Push to ECR') {
            steps {
                script {
                    sh """
                        # Login to ECR
                        aws ecr get-login-password --region ${AWS_REGION} | \
                            docker login --username AWS --password-stdin ${ECR_REGISTRY}

                        # Tag images
                        docker tag ${APP_NAME}:${IMAGE_TAG} ${ECR_REGISTRY}/${APP_NAME}:${IMAGE_TAG}
                        docker tag ${APP_NAME}:${IMAGE_TAG} ${ECR_REGISTRY}/${APP_NAME}:latest

                        # Push images
                        docker push ${ECR_REGISTRY}/${APP_NAME}:${IMAGE_TAG}
                        docker push ${ECR_REGISTRY}/${APP_NAME}:latest

                        echo "Images pushed successfully to ECR"
                    """
                }
            }
        }

        stage('Deploy to EKS') {
            steps {
                withCredentials([string(credentialsId: 'database-url', variable: 'DATABASE_URL')]) {
                    script {
                        sh """
                            # Update kubeconfig
                            aws eks update-kubeconfig --region ${AWS_REGION} --name ${EKS_CLUSTER_NAME}

                            # Create namespace if it doesn't exist
                            kubectl create namespace ${K8S_NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

                            # Create/update secrets from Jenkins credentials (not from Git)
                            kubectl create secret generic task-manager-secrets \
                                --from-literal=database-url="${DATABASE_URL}" \
                                -n ${K8S_NAMESPACE} \
                                --dry-run=client -o yaml | kubectl apply -f -

                            # Update image tag in deployment
                            sed -i 's|IMAGE_PLACEHOLDER|${ECR_REGISTRY}/${APP_NAME}:${IMAGE_TAG}|g' kubernetes/deployment.yaml

                            # Apply Kubernetes manifests (skip secrets.yaml - created above)
                            kubectl apply -f kubernetes/deployment.yaml -n ${K8S_NAMESPACE}
                            kubectl apply -f kubernetes/service.yaml -n ${K8S_NAMESPACE}
                            kubectl apply -f kubernetes/hpa.yaml -n ${K8S_NAMESPACE}

                            # Wait for deployment to complete
                            kubectl rollout status deployment/${APP_NAME} -n ${K8S_NAMESPACE} --timeout=300s
                        """
                    }
                }
            }
        }

        stage('Verify Deployment') {
            steps {
                script {
                    sh """
                        kubectl get pods -n ${K8S_NAMESPACE} -l app=${APP_NAME}
                        kubectl get svc -n ${K8S_NAMESPACE}

                        # Get the service endpoint
                        echo "Application deployed successfully!"
                        kubectl get svc ${APP_NAME} -n ${K8S_NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' || true
                    """
                }
            }
        }
    }

    post {
        always {
            node('') {
                archiveArtifacts artifacts: '**/coverage.xml,**/test-results.xml,**/safety-report.json,**/trivy-report.json', allowEmptyArchive: true
                sh 'docker rmi ${APP_NAME}:${IMAGE_TAG} || true'
                cleanWs()
            }
        }
        success {
            echo "Pipeline succeeded! Image deployed successfully."
        }
        failure {
            echo "Pipeline failed! Check logs for details."
        }
    }
}
