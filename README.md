# 🌱 Superhero Iklim

**Superhero Iklim** is a web application designed to engage university students in sustainable actions through fun challenges and AI-powered feedback. Students upload images of eco-friendly activities under different sustainability themes, and the app uses machine learning to validate the relevance of their submissions. It also features gamified elements like points and leaderboards to encourage participation.

---

## 🚀 Features

- 📸 **Image Submission**: Upload photos related to five sustainability themes:
  - Commute
  - Plants
  - Recycle
  - Energy
  - Water

- 🤖 **AI Classification**: ML model checks if the image matches the selected theme.

- 🎯 **Challenges**: Special sustainability challenges to boost engagement and earn extra points.

- 🏆 **Gamification**:
  - Earn points for valid submissions
  - View leaderboards
  - Participate in special events

- 👥 **User Roles**:
  - **Students**: Submit actions, track scores, and view personal contributions.
  - **Admins**: Manage themes, challenges, view all submissions, and verify classification results.

- ✉️ **Email Activation**: Secure sign-up process with email verification.

---

## 🛠️ Tech Stack

- **Frontend**: HTML, CSS (Tailwind), JavaScript
- **Backend**: Django (Python)
- **Database**: SQLite / PostgreSQL (production)
- **ML Model**: Image classification model using TensorFlow/Keras 
- **Hosting**: Render / GitHub Pages (static), backend on Render
- **Media Storage**: Render Disk

---

## 🧪 Setup Instructions

### Prerequisites

- Python 3.10+
- pip
- virtualenv (recommended)

### 1. Clone the repository

```bash
git clone https://github.com/fasyuzz/fyp-superheroiklim.git
cd fyp-superheroiklim
