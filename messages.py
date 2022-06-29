def create_start_message(username) -> str:
    greeting_msg = f"""
Привет, {username}!
    
Self-storage - бот по аренде складского помещения.
Если вам интересны наши услуги, пожалуйста, пройдите регистрацию.

Для этого согласитесь на обработку персональных данных.
"""

    return greeting_msg
