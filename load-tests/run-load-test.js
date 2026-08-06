const autocannon = require('autocannon');

async function runLoadTest() {
    console.log("Starting Baseline Load Test...");
    console.log("- 100 Virtual Users (Connections)");
    console.log("- Running continuously for 1 minute (60 seconds)");
    console.log("Target: http://127.0.0.1:8000/ (Make sure your backend is running)\n");

    const instance = autocannon({
        url: 'http://127.0.0.1:8000/', // The URL of your local backend
        connections: 100,              // 100 concurrent virtual users
        duration: 60,                  // 1 minute (60 seconds)
        pipelining: 1,                 // 1 request per connection at a time
    });

    // Display progress every second
    autocannon.track(instance, { renderProgressBar: true });

    instance.on('done', (result) => {
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
