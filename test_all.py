"""
Test all use cases for the Financial Analyst AI
"""
import sys
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import io

from finance_crew import run_financial_analysis

# All test cases
TEST_CASES = [
    # 📈 Stock Price Charts
    ("Show Tesla stock for 3 months", "Stock Price - Single"),
    ("Plot Apple stock for 1 year", "Stock Price - Single"),
    ("NVDA stock price YTD", "Stock Price - YTD"),
    
    # 📊 Compare Multiple Stocks
    ("Compare AAPL and MSFT for 6 months", "Compare - 2 stocks"),
    ("Compare Tesla, Ford, GM stocks for 3 months", "Compare - 3 stocks"),
    
    # 📉 Trading Volume
    ("Show Amazon trading volume for 1 month", "Volume Analysis"),
    
    # 💰 Moving Averages
    ("Apple with 50-day moving average for 6 months", "Moving Average - Single"),
    ("Tesla with 20 and 50 day MA for 3 months", "Moving Average - Multiple"),
    
    # 🇮🇳 Indian Stocks
    ("Show Reliance stock for 3 months", "Indian Stock - Reliance"),
    ("Compare TCS and Infosys for 6 months", "Indian Stock - Compare"),
]

def test_code_execution(code: str) -> tuple[bool, str]:
    """Try to execute the generated code"""
    try:
        # Remove plt.show() for headless execution
        code_modified = code.replace("plt.show()", "")
        
        # Close existing figures
        plt.close('all')
        
        # Suppress output
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
        
        # Execute
        exec(code_modified, {
            "plt": plt,
            "yf": __import__("yfinance"),
            "pd": __import__("pandas"),
            "np": __import__("numpy"),
            "datetime": __import__("datetime"),
        })
        
        # Restore
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
        # Check if a figure was created
        fig = plt.gcf()
        if fig.get_axes():
            plt.close('all')
            return True, "Chart generated successfully"
        else:
            plt.close('all')
            return False, "No chart was generated"
            
    except Exception as e:
        sys.stdout = old_stdout if 'old_stdout' in dir() else sys.__stdout__
        sys.stderr = old_stderr if 'old_stderr' in dir() else sys.__stderr__
        return False, str(e)


def run_tests():
    """Run all test cases"""
    print("=" * 80)
    print("FINANCIAL ANALYST AI - TEST SUITE")
    print("=" * 80)
    
    results = []
    
    for i, (query, category) in enumerate(TEST_CASES, 1):
        print(f"\n[{i}/{len(TEST_CASES)}] Testing: {category}")
        print(f"Query: {query}")
        print("-" * 40)
        
        # Generate code
        code = run_financial_analysis(query)
        
        if code.startswith("Error:"):
            print(f"❌ GENERATION FAILED: {code}")
            results.append((category, query, False, code))
            continue
        
        # Show first 5 lines of code
        code_preview = '\n'.join(code.split('\n')[:5])
        print(f"Code preview:\n{code_preview}\n...")
        
        # Try to execute
        success, message = test_code_execution(code)
        
        if success:
            print(f"✅ PASSED: {message}")
            results.append((category, query, True, message))
        else:
            print(f"❌ FAILED: {message}")
            print(f"Full code:\n{code}")
            results.append((category, query, False, message))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in results if r[2])
    failed = len(results) - passed
    
    print(f"\n✅ Passed: {passed}/{len(results)}")
    print(f"❌ Failed: {failed}/{len(results)}")
    
    if failed > 0:
        print("\nFailed tests:")
        for category, query, success, message in results:
            if not success:
                print(f"  - {category}: {message[:50]}...")
    
    return results


if __name__ == "__main__":
    run_tests()
