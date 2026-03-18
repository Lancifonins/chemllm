if __name__ == "__main__":
    test_cas = "64-17-5" # Ethanol
    print(f"Testing CAS: {test_cas}")
    result = get_compound_by_cas(test_cas)
    print(result)