pipeline {
    agent any
    environment {
        LAMBDA_LAYER_NAME = "python-dependencies"
        LAMBDA_FUNCTION_NAME = "error_narrative_sheet"
        S3_BUCKET_NAME = "error-narrative-sheet"
        PYTHON_RUNTIME = "python3.10"
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