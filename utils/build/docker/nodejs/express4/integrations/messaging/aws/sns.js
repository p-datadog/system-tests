const AWS = require('aws-sdk')

let TopicArn
let QueueUrl

const snsPublish = (queue, topic, message) => {
  // Create an SQS client
  const sns = new AWS.SNS({
    endpoint: 'http://localstack:4566',
    region: 'us-east-1'
  })
  const sqs = new AWS.SQS({
    endpoint: 'http://localstack:4566',
    region: 'us-east-1'
  })

  const messageToSend = message ?? 'Hello from SNS JavaScript injection'

  return new Promise((resolve, reject) => {
    sns.createTopic({ Name: topic }, (err, data) => {
      if (err) {
        console.log(err)
        reject(err)
      }

      TopicArn = data.TopicArn

      sqs.createQueue({ QueueName: queue }, (err, res) => {
        if (err) {
          console.log(err)
          reject(err)
        }

        QueueUrl = data.QueueUrl

        sqs.getQueueAttributes({ QueueUrl, AttributeNames: ['All'] }, (err, data) => {
          if (err) {
            console.log(err)
            reject(err)
          }

          const subParams = {
            Protocol: 'sqs',
            Endpoint: data.Attributes.QueueArn,
            TopicArn
          }

          sns.subscribe(subParams, (err) => {
            if (err) {
              console.log(err)
              reject(err)
            }

            // Send messages to the queue
            const produce = () => {
              sns.publish({ TopicArn, MessageBody: messageToSend }, (err, data) => {
                if (err) {
                  console.log(err)
                  reject(err)
                }

                console.log(data)
                resolve()
              })
              console.log('Published a message from JavaScript SNS')
            }

            // Start producing messages
            produce()
          })
        })
      })
    })
  })
}

const snsConsume = async (queue, timeout) => {
  // Create an SQS client
  const sqs = new AWS.SQS({
    endpoint: 'http://localstack:4566',
    region: 'us-east-1'
  })

  const queueUrl = `http://localstack:4566/000000000000/${queue}`

  return new Promise((resolve, reject) => {
    sqs.receiveMessage({
      QueueUrl: queueUrl,
      MaxNumberOfMessages: 1,
      MessageAttributeNames: ['.*']
    }, (err, response) => {
      if (err) {
        console.error('[SNS->SQS] Error receiving message: ', err)
        reject(err)
      }

      try {
        console.log(response)
        if (response && response.Messages) {
          for (const message of response.Messages) {
            const consumedMessage = message.Body
            console.log('[SNS->SQS] Consumed the following: ' + consumedMessage)
          }
          resolve()
        } else {
          console.log('[SNS->SQS] No messages received')
        }
      } catch (error) {
        console.error('[SNS->SQS] Error while consuming messages: ', error)
        reject(err)
      }
    })
    setTimeout(() => {
      reject(new Error('[SNS->SQS] Message not received'))
    }, timeout) // Set a timeout of n seconds for message reception
  })
}

module.exports = {
  snsPublish,
  snsConsume
}
