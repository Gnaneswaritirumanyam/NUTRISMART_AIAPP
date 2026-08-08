const ExcelJS = require('exceljs');

async function generateTestCases() {
    const workbook = new ExcelJS.Workbook();
    workbook.creator = 'Selenium Automated Generator';
    workbook.created = new Date();

    const sheet = workbook.addWorksheet('Web Test Cases');
    
    // Define columns
    sheet.columns = [
        { header: 'Test Case ID', key: 'id', width: 15 },
        { header: 'Module', key: 'module', width: 20 },
        { header: 'Test Scenario', key: 'scenario', width: 40 },
        { header: 'Test Steps', key: 'steps', width: 50 },
        { header: 'Expected Result', key: 'expected', width: 40 },
        { header: 'Priority', key: 'priority', width: 15 },
        { header: 'Status', key: 'status', width: 15 }
    ];

    // Style the header row
    sheet.getRow(1).font = { bold: true };

    const testCases = [];
    let tcId = 1;

    const modules = {
        "Authentication": ["Login valid", "Login invalid", "Empty credentials", "SQL injection in login", "Session timeout", "Logout"],
        "Responsive Design": ["Desktop view rendering", "Mobile view rendering", "Tablet view rendering", "Navbar hamburger toggle", "Image scaling"],
        "Dashboard": ["Data fetch on load", "Mocked API fallback", "Chart rendering", "Widget refresh", "Profile dropdown"],
        "Fitness & Diet": ["Form submission (new meal)", "Input validation (calories)", "List dynamic update", "Delete item", "Filter items"],
        "AI Chat": ["Send valid prompt", "Empty prompt", "WebSockets connection", "Auto-scroll on new message", "Typing indicator"],
        "Cross-Browser": ["Chrome compatibility", "Firefox compatibility", "Edge compatibility", "Safari compatibility"],
        "Security": ["XSS payload in inputs", "CORS policy check", "Content Security Policy (CSP)", "Local storage encryption"],
        "Profile & Settings": ["Update email", "Change password", "Upload avatar", "Delete account", "Toggle theme", "Notification preferences"]
    };

    const edgeCases = [
        "with normal usage",
        "with slow 3G network simulation",
        "with offline mode simulation",
        "with large data payloads",
        "with special characters input",
        "with concurrent requests",
        "with aggressive double-clicking",
        "with expired JWT token"
    ];

    const priorities = ["High", "Medium", "Low", "Critical"];

    // Generate base cases + edge cases combination
    for (const [moduleName, features] of Object.entries(modules)) {
        for (const feature of features) {
            for (const edge of edgeCases) {
                // Determine priority
                let priority = priorities[Math.floor(Math.random() * priorities.length)];
                if (feature.includes("injection") || feature.includes("Security") || edge.includes("token")) {
                    priority = "Critical";
                }

                testCases.push({
                    id: `WEB_TC_${String(tcId).padStart(4, '0')}`,
                    module: moduleName,
                    scenario: `Verify ${feature} ${edge}`,
                    steps: `1. Open web application. 2. Navigate to ${moduleName}. 3. Execute ${feature} ${edge}.`,
                    expected: `Application should handle the scenario appropriately without crashing or exposing sensitive data.`,
                    priority: priority,
                    status: 'Not Executed'
                });
                tcId++;
            }
        }
    }

    // Add E2E flow cases
    const e2eFlows = [
        "Login -> Navigate Dashboard -> Add Meal -> Verify Diet List -> Logout",
        "Signup -> Mobile View -> Open AI Chat -> Prompt -> Receive Response -> Auto-scroll check",
        "Login -> Offline mode -> Try fetching Dashboard -> Verify fallback UI"
    ];

    for (const flow of e2eFlows) {
        testCases.push({
            id: `WEB_TC_${String(tcId).padStart(4, '0')}`,
            module: "E2E Workflows",
            scenario: `Verify complete flow: ${flow}`,
            steps: `Execute steps in sequence: ${flow}`,
            expected: "Flow completes successfully.",
            priority: "High",
            status: "Not Executed"
        });
        tcId++;
    }

    // Add to sheet
    sheet.addRows(testCases);

    const filename = 'Web_Test_Cases.xlsx';
    await workbook.xlsx.writeFile(filename);
    console.log(`Successfully generated ${testCases.length} web test cases in ${filename}`);
}

generateTestCases().catch(err => {
    console.error("Error generating test cases:", err);
});
