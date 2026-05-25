const mysql = require('mysql2/promise');
const redis = require('redis');

// MySQL Connection Pool
const pool = mysql.createPool({
    host: process.env.MYSQL_HOST,
    port: process.env.MYSQL_PORT,
    user: process.env.MYSQL_USER,
    password: process.env.MYSQL_PASSWORD,
    database: process.env.MYSQL_DATABASE,
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});

// Redis Client
const redisClient = redis.createClient({
    url: `redis://${process.env.REDIS_HOST}:${process.env.REDIS_PORT}`
});

redisClient.on('error', (err) => console.log('Redis Error:', err));
redisClient.on('connect', () => console.log('✅ Redis Connected'));

redisClient.connect();

module.exports = { pool, redisClient };