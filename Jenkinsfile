pipeline {
    agent any
    environment {
        LAMBDA_LAYER_NAME = "python-dependencies"
        LAMBDA_FUNCTION_NAME = "error_narrative_sheet"
        S3_BUCKET_NAME = "error-narrative-sheet"
        PYTHON_RUNTIME = "python3.10"
        PATH = "${PATH}:/var/lib/jenkins/.sonar/sonar-scanner-4.7.0.2747-linux/bin"
    }
    parameters { 
        string(name: 'OnlineErrorCode', defaultValue: 'ONLINE-001', description: 'Enter the online error code') 
        string(name: 'BatchErrorCode', defaultValue: 'BATCH-001', description: 'Enter the batch error code') 
        string(name: 'ErrorDescription', defaultValue: 'Sample Error Code', description: 'Enter the error narration') 
    }
    stages {
        stage ("Clean Workspace") {
            steps {
                script {
                    cleanWs()
                }
            }
        }
        stage ("Source code checkout") {
            steps {
                script {
                    git branch: 'main', url: 'https://github.com/SubrahmanyamRaparti/boto3-s3-lambda-cicd.git'
                }
            }
        }
        stage ("Static Code Analysis - Sonar Cloud") {
            environment {
                SONAR_TOKEN = sonar_token()
            }
            steps {
                withSonarQubeEnv('SonarCloud') {
                    sh '''
                        sonar-scanner \
                          -Dsonar.organization=subrahmanyam \
                          -Dsonar.projectKey=subrahmanyam_error-narrative-report \
                          -Dsonar.sources=. \
                          -Dsonar.token=${SONAR_TOKEN} \
                          -Dsonar.host.url=https://sonarcloud.io
                    '''
                }
            }
        }
        stage("Quality Gate") {
            steps {
                timeout(time: 1, unit: 'HOURS') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }
        stage ("Check if S3 bucket exists") {
            steps {
                sh '''
                    aws s3 ls | grep -q ${S3_BUCKET_NAME} || exit 254
                    mkdir python_volume
                '''
            }
        }
        stage ("Update lambda function code") {
            when { 
                changeset "lambda_function.py"
            }
            steps {
                sh '''
                    zip ${LAMBDA_FUNCTION_NAME}.zip lambda_function.py
                    
                    aws lambda update-function-code \
                        --function-name ${LAMBDA_FUNCTION_NAME} \
                        --zip-file fileb://${LAMBDA_FUNCTION_NAME}.zip
                '''
            }
        }
        stage("Build dependencies") {
            agent {
                docker {
                    image "public.ecr.aws/sam/build-${PYTHON_RUNTIME}:latest"
                    reuseNode true
                }
            }
            when { 
                changeset "requirement.txt"
            }
            steps {
                dir('python_volume') {
                    sh '''
                        installation_path=python
                        mkdir $installation_path
                        pip3 install -r ../requirement.txt --upgrade -t $installation_path
                        zip -r lambda-layer.zip * -x '*/__pycache__/*'
                        aws s3 cp lambda-layer.zip s3://${S3_BUCKET_NAME}/
                    '''
                }
            }
        }
        stage("Update lambda layer & function") {
            when { 
                changeset "requirement.txt"
            }
            steps {
                dir('python_volume') {
                    sh '''
                        publish_layer_response=$(aws lambda publish-layer-version \
                            --layer-name "${LAMBDA_LAYER_NAME}" \
                            --description "Error Narrative Sheet" \
                            --license-info "MIT" \
                            --content S3Bucket=${S3_BUCKET_NAME},S3Key=lambda-layer.zip \
                            --compatible-runtimes "${PYTHON_RUNTIME}")

                        publish_layer_response_arn=$(echo ${publish_layer_response} | jq -r .LayerVersionArn)
                        
                        aws lambda update-function-configuration \
                            --function-name ${LAMBDA_FUNCTION_NAME} \
                            --layers ${publish_layer_response_arn}
                    '''
                }
            }
        }
        stage("Update lambda function environment variables") {
            environment {
                ONLINE_CODE = online_code()
                BATCH_CODE = batch_code()
                ERROR_DESCRIPTION = error_description()
            }
            steps {
                    sh '''
                        aws lambda update-function-configuration \
                            --function-name ${LAMBDA_FUNCTION_NAME} \
                            --environment "Variables={ONLINE_CODE=${ONLINE_CODE}, BATCH_CODE=${BATCH_CODE}, ERROR_DESCRIPTION=${ERROR_DESCRIPTION}}"
                    '''
            }
        }
        stage("Invoke lambda function") {
            steps {
                    sh '''
                        aws lambda invoke \
                            --function-name ${LAMBDA_FUNCTION_NAME} \
                            --cli-binary-format raw-in-base64-out response.json
                        cat response.json
                    '''
            }
        }
    }
}

def online_code() {
    def online_code = sh returnStdout: true, script: "echo ${params.OnlineErrorCode}"
    return online_code
}

def batch_code() {
    def online_code = sh returnStdout: true, script: "echo ${params.BatchErrorCode}"
    return online_code
}

def error_description() {
    def online_code = sh returnStdout: true, script: "echo ${params.ErrorDescription}"
    return online_code
}

def sonar_token() {
    def sonar_token = sh returnStdout: true, script: "aws ssm get-parameter --name /cicd/sonartoken --with-decryption --region ap-south-1 | jq -r .Parameter.Value"
    return sonar_token
}