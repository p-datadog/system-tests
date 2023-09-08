"use strict";

const tracer = require('dd-trace').init({
  debug: true
});

const app = require("express")();
const { Kafka } = require("kafkajs")
const axios = require('axios');
const fs = require('fs');
const passport = require('passport')


app.use(require("body-parser").json());
app.use(require("body-parser").urlencoded({ extended: true }));
app.use(require("express-xml-bodyparser")());
app.use(require("cookie-parser")());

app.get("/", (req, res) => {
  console.log("Received a request");
  res.send("Hello\n");
});

app.all(["/waf", "/waf/*"], (req, res) => {
  res.send("Hello\n");
});

app.get("/sample_rate_route/:i", (req, res) => {
  res.send("OK");
});

app.get("/params/:value", (req, res) => {
  res.send("OK");
});

app.get("/headers", (req, res) => {
  res.set({
    "content-type": "text/plain",
    "content-length": "42",
    "content-language": "en-US",
  });

  res.send("Hello, headers!");
});

app.get("/identify", (req, res) => {
  tracer.setUser({
    id: "usr.id",
    email: "usr.email",
    name: "usr.name",
    session_id: "usr.session_id",
    role: "usr.role",
    scope: "usr.scope",
  });

  res.send("OK");
});

app.get("/status", (req, res) => {
  res.status(parseInt(req.query.code)).send("OK");
});

app.get("/make_distant_call", (req, res) => {
  const url = req.query.url;
  console.log(url);

  axios.get(url)
    .then(response => {
      res.json({
        url: url,
        status_code: response.statusCode,
        request_headers: null,
        response_headers: null,
      });
    })
    .catch(error => {
      console.log(error);
      res.json({
        url: url,
        status_code: 500,
        request_headers: null,
        response_headers: null,
      });
    });
});

app.get("/user_login_success_event", (req, res) => {
  const userId = req.query.event_user_id || "system_tests_user";

  tracer.appsec.trackUserLoginSuccessEvent({
    id: userId,
    email: "system_tests_user@system_tests_user.com",
    name: "system_tests_user"
  }, { metadata0: "value0", metadata1: "value1" });

  res.send("OK");
});

app.get("/user_login_failure_event", (req, res) => {
  const userId = req.query.event_user_id || "system_tests_user";
  let exists = true;
  if (req.query && req.query.hasOwnProperty("event_user_exists")) {
    exists = req.query.event_user_exists.toLowerCase() === "true"
  }

  tracer.appsec.trackUserLoginFailureEvent(userId, exists, { metadata0: "value0", metadata1: "value1" });

  res.send("OK");
});

app.get("/custom_event", (req, res) => {
  const eventName = req.query.event_name || "system_tests_event";

  tracer.appsec.trackCustomEvent(eventName, { metadata0: "value0", metadata1: "value1" });

  res.send("OK");
});

app.get("/users", (req, res) => {
  let user = {}
  if (req.query['user']) {
    user.id = req.query['user']
  } else {
    user.id = 'anonymous'
  }

  const shouldBlock = tracer.appsec.isUserBlocked(user)
  if (shouldBlock) {
    tracer.appsec.blockRequest(req, res)
  } else {
    res.send(`Hello ${user.id}`)
  }
});

app.get("/dsm", (req, res) => {
  const kafka = new Kafka({
    clientId: 'my-app',
    brokers: ['kafka:9092'],
    retry: {
      initialRetryTime: 100, // Time to wait in milliseconds before the first retry
      retries: 20, // Number of retries before giving up
    },
  })
  const producer = kafka.producer()
  const doKafkaOperations = async () => {
    await producer.connect()
    await producer.send({
      topic: 'dsm-system-tests-queue',
      messages: [
        { value: 'hello world!' },
      ],
    })
    await producer.disconnect()

    const consumer = kafka.consumer({ groupId: 'testgroup1' })

    await consumer.connect()
    await consumer.subscribe({ topic: 'dsm-system-tests-queue', fromBeginning: true })

    await consumer.run({
      eachMessage: async ({topic, partition, message}) => {
        console.log({
          value: message.value.toString(),
        });
        await consumer.stop();
        await consumer.disconnect();
      },
    })
  }
  doKafkaOperations()
      .then(() => {
        res.send('ok');
      })
      .catch((error) => {
        console.error(error);
        res.status(500).send('Internal Server Error');
      });
});

app.get('/load_dependency', (req, res) => {
  console.log('Load dependency endpoint');
  const glob = require("glob")
  res.send("Loaded a dependency")
});

app.all('/tag_value/:tag/:status', (req, res) => {
  require('dd-trace/packages/dd-trace/src/plugins/util/web').root(req).setTag('appsec.events.system_tests_appsec_event.value', req.params.tag);

  for (const [k, v] of Object.entries(req.query)) {
    res.set(k, v);
  }

  res.status(req.params.status || 200).send('Value tagged');
});

app.get('/read_file', (req, res) => {
  const path = req.query['file'];
  fs.readFile(path, (err, data) => {
    if (err) {
      console.error(err);
      res.status(500).send("ko");
    }
    res.send(data);
  });
});

var integration_db_initialized=false

app.get('/db', (req, res) => {
  console.log("Service: " + req.query.service)
  console.log("Operation: " + req.query.operation)

  const pgsql = require('./integrations/db/postgres');
  const mysql = require('./integrations/db/mysql');
  const mssql = require('./integrations/db/mssql');

  if (!integration_db_initialized){
    console.log('Initializing DBs');
    integration_db_initialized=true
    pgsql.init();
    mysql.init();
    mssql.init();
  }

  if (req.query.service == "postgresql") {
    pgsql.doOperation(req.query.operation)
  }else  if (req.query.service == "mysql") {
    mysql.doOperation(req.query.operation)
  }else  if (req.query.service == "mssql") {
    mssql.doOperation(req.query.operation)
  }

});

require("./iast")(app, tracer);
require('./auth')(app, passport, tracer)
require('./graphql')(app)

app.listen(7777, '0.0.0.0', () => {
  tracer.trace('init.service', () => {});
  console.log('listening');
});
