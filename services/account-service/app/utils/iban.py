import random


def generate_account_number() -> str:
    return "".join([str(random.randint(0, 9)) for _ in range(16)])


def generate_iban(country_code: str = "MA", account_number: str = None) -> str:
    if not account_number:
        account_number = generate_account_number()

    bank_code = "00155"
    branch_code = "00101"
    account_part = account_number.zfill(11)
    key = "00"

    bban = f"{bank_code}{branch_code}{account_part}{key}"

    rearranged = bban + country_code + "00"
    numeric = ""
    for char in rearranged:
        if char.isalpha():
            numeric += str(ord(char) - ord("A") + 10)
        else:
            numeric += char

    check_digits = 98 - (int(numeric) % 97)
    check_str = str(check_digits).zfill(2)

    return f"{country_code}{check_str}{bban}"
