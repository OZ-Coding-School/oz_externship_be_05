import random
from django.utils import timezone
from datetime import timedelta

def generate_code(length=6):
	"""
	6자리 랜덤 숫자 코드 생성함
	
	:param length: 코드 길이
	"""
	return "".join(str(random.randint(0, 9)) for _ in range(length))

def expiry(minutes=5):
	"""
	만료시간 뱉음
	
	:param miniutes: 몇 분 후 만료인지
	"""
	return timezone.now() + timedelta(minutes=minutes)

def send_sms(phone_number):
	"""
	SMS 전송하는 함수 (미구현)
	
	:param phone_number: 수신자 번호
	:param code: 인증 코드
	"""
	print(f"{phone_number} - {code}")
	pass