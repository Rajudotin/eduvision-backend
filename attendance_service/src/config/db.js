const mysql = require('mysql2/promise');
const redis = require('redis');

// MySQL Connection Pool
const pool = mysql.createPool({
    host: process.env.MYSQL_HOST || 'localhost',
    port: process.env.MYSQL_PORT || 3306,
    user: process.env.MYSQL_USER || 'root',
    password: process.env.MYSQL_PASSWORD || '',
    database: process.env.MYSQL_DATABASE || 'eduvision',
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});

// Redis Client
const redisClient = redis.createClient({
    url: `redis://${process.env.REDIS_HOST || 'localhost'}:${process.env.REDIS_PORT || 6379}`
});

redisClient.on('error', (err) => console.log('Redis Error:', err));
redisClient.on('connect', () => console.log('✅ Redis Connected'));

redisClient.connect();

// Test MySQL connection
pool.getConnection()
    .then(conn => {
        console.log('✅ MySQL Connected');
        conn.release();
    })
    .catch(err => {
        console.error('❌ MySQL Connection Failed:', err.message);
    });

module.exports = { pool, redisClient };