import unittest

from fastapi import HTTPException
from app.services.group_safety import contains_phone_number, validate_group_text

class GroupSafetyTests(unittest.TestCase):
    def test_blocks_sri_lankan_phone_variants(self):
        blocked=["0771234567","+94771234567","0094771234567","077 123 4567","(077) 123-4567","+94 (77) 123 4567"]
        for value in blocked:
            with self.subTest(value=value): self.assertTrue(contains_phone_number(value))

    def test_blocks_common_explicit_international_numbers(self):
        self.assertTrue(contains_phone_number("+1 (415) 555-2671"))
        self.assertTrue(contains_phone_number("0044 7700 900123"))

    def test_allows_ordinary_academic_numbers(self):
        allowed=["I scored 75 out of 100","Lesson 12, exercise 4","2026-08-14","12 + 15 = 27","Page 123456"]
        for value in allowed:
            with self.subTest(value=value): self.assertFalse(contains_phone_number(value))

    def test_rejected_content_is_not_reflected(self):
        secret="077 123 4567"
        with self.assertRaises(HTTPException) as caught: validate_group_text(secret)
        self.assertNotIn(secret,caught.exception.detail)

if __name__ == "__main__": unittest.main()
