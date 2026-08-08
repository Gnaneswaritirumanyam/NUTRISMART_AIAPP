import csv
import os

def generate_test_cases():
    test_cases = []
    
    categories = {
        "Authentication": 40,
        "Authorization": 40,
        "Navigation": 30,
        "UI_Validation": 50,
        "Forms": 50,
        "CRUD_Operations": 50,
        "Input_Validation": 40,
        "Error_Handling": 20,
        "Session_Management": 20,
        "File_Upload": 20,
        "Accessibility": 20,
        "Responsive_Design": 20,
        "Performance_Smoke": 20,
        "Regression": 50
    }

    test_id_counter = 1
    
    for category, count in categories.items():
        for i in range(count):
            test_id = f"TC_{category.upper()}_{i+1:03d}"
            
            # Simple alternating logic to simulate different expected outcomes
            if i % 5 == 0:
                expected_status = "failure_expected"
                status = "fail"
            elif i % 15 == 0:
                expected_status = "skipped_expected"
                status = "skip"
            else:
                expected_status = "success_expected"
                status = "pass"
                
            test_cases.append({
                "test_id": test_id,
                "category": category,
                "module": f"{category}_Module",
                "test_name": f"Validate {category} behavior {i+1}",
                "priority": "High" if i % 10 == 0 else "Medium",
                "expected_status": expected_status,
                "mock_status": status
            })
            
            test_id_counter += 1

    # Ensure directories exist
    os.makedirs('automation/data', exist_ok=True)
    
    with open('automation/data/test_cases.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["test_id", "category", "module", "test_name", "priority", "expected_status", "mock_status"])
        writer.writeheader()
        writer.writerows(test_cases)
        
    print(f"Successfully generated {len(test_cases)} test cases.")

if __name__ == "__main__":
    generate_test_cases()
