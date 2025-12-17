# Agario Clone

Онлайн-гра типу Agar.io на Python з **Socket.IO** та **Pygame**.  
Сервер підтримує реальні оновлення гравців через **WebSockets**.

---

## => Файли проекту

- `app.py` – сервер гри на Python + Eventlet + Socket.IO  
- `requirements.txt` – список модулів 
- `client.py` – клієнт у якому ОБОВ'ЯЗКОВО потрібно поставити свою адресу хосту

---

## => Render – налаштування Web Service

1. **Створити Web Service** в Render.  
2. **GitHub repo:** підключити репозиторій проекту.  
3. **Build Command:**  
   ```bash
   pip install -r requirements.txt
4. **Start Command:**  
   ```bash
   python app.py

