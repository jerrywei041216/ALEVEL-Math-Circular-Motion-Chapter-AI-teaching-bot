# ALEVEL-Math-Circular-Motion-Chapter-AI-teaching-bot
AI-powered automation system that reads email attachments, understands math/physics problems from images, and automatically generates Manim animated teaching videos with detailed solution scripts.

AI Teaching Bot – Automated Problem-Solving + Manim Video Generator
This project is an end-to-end automation system that transforms email-based problem submissions into fully animated Manim teaching videos and detailed step-by-step solution scripts.
It uses GPT-5.1 (vision-enabled) to interpret screenshot-based questions, generate reasoning, produce runnable Manim animation code, and render an instructional video — all triggered automatically when a new email with a specific subject arrives.

✨ Key Features
📩 Email Listener: Monitors Gmail via IMAP and detects new “teaching” requests
🖼️ Vision-Based Problem Recognition: Reads math/physics questions from screenshots
🧠 AI Reasoning Engine: Generates rigorous step-by-step explanations
🎬 Manim Video Generator: Produces animated teaching videos automatically
📝 Solution Script Writer: Outputs detailed student-friendly explanation text
🔁 Fully Automated Pipeline: From email → AI → Manim → video output
🎯 Zero Manual Intervention: Runs continuously as an autonomous teaching assistant
This system can be extended into a personal AI tutor, classroom assistant, or a fully automated video-generation workflow for educational content creators.

1. automatically_teaching.py — Core Teaching Video Generator
This script is responsible for transforming a problem screenshot into a complete educational package.
Functions:
Accepts an image (either from email_watcher or local testing)
Sends the screenshot to GPT-5.1 (with vision)
Generates:
📝 A detailed, student-friendly step-by-step explanation (solution_script.txt)
🎬 Fully runnable Manim animation code (solution_scene.py)
Automatically renders the Manim animation into a high-quality teaching video
Saves all outputs locally and cleans up temporary files
Purpose:
This is the brain of the system — it handles all AI reasoning, explanation generation, and Manim animation production.

2. email_watcher.py — Automated Email Listener & Trigger
This script monitors your Gmail inbox and automatically triggers the teaching pipeline when a new problem is received.
Functions:
Connects to Gmail via IMAP
Monitors for new emails from a specific sender 
Filters emails with the exact subject
Extracts the attached problem screenshot (JPG/PNG)
Automatically calls automatically_teaching.py to generate:
A full Manim teaching video
A detailed solution script
Purpose:
This script transforms your Gmail inbox into an automated “submission portal” —
sending an email with a problem screenshot instantly triggers the entire AI teaching workflow.
