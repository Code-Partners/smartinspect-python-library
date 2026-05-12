pipeline {
    agent {
        docker {
            image 'ubuntu:noble'
        }
    }
    triggers{
        githubPush()
    }
    stages {
        stage('Trigger e2e tests') {
          steps {
            build job: "../smartinspect-e2e-tests-python/dev", parameters: [
              [$class: 'StringParameterValue', name: 'TRIGGER_BRANCH_NAME', value: String.valueOf(BRANCH_NAME)]
            ]
          }
        }
    }
}