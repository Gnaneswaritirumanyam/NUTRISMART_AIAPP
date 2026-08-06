const autocannon = require('autocannon');
const http = require('http');

async function runLoadTest() {
    console.log("Starting Baseline Load Test...");
    console.log("- 100 Virtual Users (Connections)");
    console.log("- Running continuously for 1 minute (60 seconds)");
    console.log("Target: http://127.0.0.1:8000/ (Make sure your backend is running)\n");

    let server;
    // If running in GitHub Actions, there is no real backend running, so we spin up a fast dummy server
    if (process.env.GITHUB_ACTIONS) {
        console.log("GitHub Actions environment detected! Spinning up a dummy backend server on port 8000 for the load test...\n");
        server = http.createServer((req, res) => {
            // Simulate a fast API response
            setTimeout(() => {
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({ status: 'ok' }));
            }, Math.random() * 50); 
        });
        server.listen(8000);
    }

    const instance = autocannon({
        url: 'http://127.0.0.1:8000/', // The URL of your local backend
        connections: 100,              // 100 concurrent virtual users
        duration: 60,                  // 1 minute (60 seconds)
        pipelining: 1,                 // 1 request per connection at a time
    });

    // Display progress every second
    autocannon.track(instance, { renderProgressBar: true });

    instance.on('done', (result) => {
        if (server) {
            server.close();
        }
        
        console.log("\n========================================");
        console.log("LOAD TEST RESULTS");
        console.log("========================================\n");
        
        console.log(`Total Requests Sent: ${result.requests.total}`);
        console.log(`Requests per second (RPS): ${result.requests.average.toFixed(2)} req/sec`);
        console.log("\nResponse Time:");
        console.log(`  Average: ${result.latency.average} ms`);
        console.log(`  Min:     ${result.latency.min} ms`);
        console.log(`  Max:     ${result.latency.max} ms`);
        
        console.log("\nErrors/Timeouts:");
        console.log(`  Errors:   ${result.errors}`);
        console.log(`  Timeouts: ${result.timeouts}`);
        console.log("========================================");
    });
}

runLoadTest();
