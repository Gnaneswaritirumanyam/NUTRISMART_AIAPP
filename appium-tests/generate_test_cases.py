import openpyxl
import random

def generate_test_cases():
    test_cases = []
    tc_id = 1
    
    modules = {
        "Authentication": ["Login", "Sign Up", "Forgot Password", "Session Timeout", "OAuth Login"],
        "Onboarding": ["Splash Screen", "Permissions Request", "Tutorial Intro"],
        "Dashboard": ["Widget Load", "Navigation Menu", "Pull to Refresh", "Offline mode notification", "User Avatar"],
        "Fitness": ["Add Workout", "Edit Workout", "Delete Workout", "View History", "Sync with smartwatch"],
        "Diet": ["Add Meal", "Search Recipe", "Filter by Cuisine", "View Ingredients", "Calorie calculation"],
        "Budget": ["Set Budget limit", "View Expenses", "Add Expense", "Category breakdown chart"],
        "AI Chat": ["Send prompt", "Receive response", "Network error handling", "Clear chat history", "Voice input"],
        "Profile": ["Update Email", "Change Password", "Upload Profile Picture", "Toggle Dark Mode", "Delete Account"]
    }
    
    edge_cases = [
        "with empty fields",
        "with extremely long string inputs",
        "with special characters",
        "with SQL injection payloads",
        "with XSS payloads",
        "while device is offline",
        "with poor network connection",
        "while switching apps (background to foreground)",
        "with screen rotation (portrait to landscape)",
        "with low battery mode enabled",
        "with rapid multiple clicks",
        "with invalid data formats"
    ]
    
    priorities = ["High", "Medium", "Low"]
    
    # Base cases
    for module, features in modules.items():
        for feature in features:
            test_cases.append({
                "Test Case ID": f"TC_{tc_id:04d}",
                "Module": module,
                "Test Scenario": f"Verify successful {feature}",
                "Test Steps": f"1. Navigate to {module}. 2. Initiate {feature}. 3. Provide valid inputs. 4. Submit.",
                "Expected Result": f"{feature} should execute successfully.",
                "Priority": "High",
                "Status": "Not Executed"
            })
            tc_id += 1
            
            for edge in edge_cases:
                priority = random.choice(priorities)
                if "SQL" in edge or "XSS" in edge:
                    priority = "High"
                
                test_cases.append({
                    "Test Case ID": f"TC_{tc_id:04d}",
                    "Module": module,
                    "Test Scenario": f"Verify {feature} {edge}",
                    "Test Steps": f"1. Navigate to {module}. 2. Initiate {feature} {edge}. 3. Submit.",
                    "Expected Result": f"System should handle the scenario gracefully without crashing. Appropriate error messages if applicable.",
                    "Priority": priority,
                    "Status": "Not Executed"
                })
                tc_id += 1
    
    # E2E Workflows
    e2e_flows = [
        ("Login -> Navigate to Dashboard -> Add Meal -> Verify Calories -> Logout", "High"),
        ("Signup -> Complete Onboarding -> Set Budget -> Add Expense -> Verify Chart", "High"),
        ("Login -> Open AI Chat -> Ask for Recipe -> Add to Diet -> Verify Dashboard", "High")
    ]
    
    for flow, prio in e2e_flows:
        test_cases.append({
            "Test Case ID": f"TC_{tc_id:04d}",
            "Module": "E2E Workflows",
            "Test Scenario": f"Verify E2E flow: {flow}",
            "Test Steps": f"Execute the following flow sequentially: {flow}",
            "Expected Result": "Flow should complete without any blocking issues.",
            "Priority": prio,
            "Status": "Not Executed"
        })
        tc_id += 1
        
    # Create Excel file using openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Test Cases"
    
    # Write Headers
    headers = ["Test Case ID", "Module", "Test Scenario", "Test Steps", "Expected Result", "Priority", "Status"]
    ws.append(headers)
    
    # Write Data
    for tc in test_cases:
        row = [tc[h] for h in headers]
        ws.append(row)
        
    filename = "Test_Cases_Summary_and_Details.xlsx"
    wb.save(filename)
    print(f"Successfully generated {len(test_cases)} test cases in {filename}")

if __name__ == "__main__":
    generate_test_cases()
