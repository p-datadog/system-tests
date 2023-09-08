"use strict";

const { join } = require('path')
const { Client, Pool } = require('pg')
const { readFileSync, statSync } = require('fs')


function initData() {
    console.log("loading sql data")
    const query = readFileSync(join(__dirname, 'resources', 'postgres.sql')).toString()
    const client = new Client()
    return client.connect().then(() => {
        return client.query(query)
    })
}

function select() {
    const sql = 'SELECT * FROM demo '
    const client = new Client()
    client.connect().then(() => {
        return client.query(sql).then((queryResult) => {
            console.log(queryResult)
        })
    }).catch((err) => {
        console.log(err)
    })
}

function update() {
    const sql = 'update demo set age=22 where id=1 '
    const client = new Client()
    client.connect().then(() => {
        return client.query(sql);
    }).catch((err) => {
        console.log(err)
    })
}

function insert() {
    const sql = "insert into demo (id,name,age) values(3,'test3',163) "
    const client = new Client()
    client.connect().then(() => {
        return client.query(sql);
    }).catch((err) => {
        console.log(err)
    })
}

function deleteSQL() {
    const sql = 'delete from demo where id=2 '
    const client = new Client()
    client.connect().then(() => {
        return client.query(sql);
    }).catch((err) => {
        console.log(err)
    })
}

function callProcedure() {
    const sql = 'call helloworld() '
    const client = new Client()
    client.connect().then(() => {
        return client.query(sql);
    }).catch((err) => {
        console.log(err)
    })
}

function selectError() {
    const sql = 'SELECT * FROM demossssss'
    const client = new Client()
    client.connect().then(() => {
        return client.query(sql).then((queryResult) => {
            console.log(queryResult)
        })
    }).catch((err) => {
        console.log(err)
    })
}
function doOperation(operation) {
    console.log("Selecting operation");
    switch (operation) {
        case "select":
            select();
            break;
        case "select_error":
            selectError();
            break;
        case "insert":
            insert();
            break;
        case "delete":
            deleteSQL();
            break;
        case "update":
            update();
            break;
        case "procedure":
            callProcedure();
            break;
        default:
            console.log("Operation " + crudOp + " not allowed");

    }
}
function init(app) {
    console.log("Initializing nodejs module");
    initData();
};
module.exports = {
    init: init,
    doOperation: doOperation
};