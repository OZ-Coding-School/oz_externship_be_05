def mask_email(email: str, keep_start: int = 1, keep_end: int = 1, mask_char: str = "*") -> str:
	"""
	이메일의 로컬 파트(@ 앞)를 일부 마스킹.
	기본 규칙: 앞 1글자 + 뒤 1글자만 남기고 나머지는 '*' 처리.

	ex) miku@gmail.com -> m**u@gmail.com

	Args:
		:keep_start: 유지할 앞 글자 수
		:keep_end: 유지할 뒤에 글자 수
		:mask_char: 마스킹에 사용할 char
	"""
	if "@" not in email:
		return email

	local, domain = email.split("@", 1)

	if keep_start < 0 or keep_end < 0:
		raise ValueError("keep_start , keep_end 값을 0이상으로 해주세요. ")

	n = len(local)
	if n == 0:
		return email

	if keep_start + keep_end >= n:
		return f"{local}@{domain}"

	start = local[:keep_start] if keep_start > 0 else ""
	end = local[-keep_end:] if keep_end > 0 else ""
	masked_len = n - (keep_start + keep_end)

	return f"{start}{mask_char * masked_len}{end}@{domain}"