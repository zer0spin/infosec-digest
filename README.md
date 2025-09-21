[![Live Demo](https://img.shields.io/badge/Live_Demo-Online-brightgreen?style=for-the-badge&logo=vercel)](https://infosec-digest.vercel.app)

## [Leia em Português (pt-BR)](README.pt-br.md)

# InfoSec Digest

**InfoSec Digest** is a modern, secure, and high-performance aggregator for cybersecurity news and podcasts. The project is built with a decoupled GitOps architecture, serving content statically for maximum security and speed, with fully automated updates.

## ✨ Features

- **Centralized Content**: Aggregates the latest news and podcast episodes from the most relevant cybersecurity sources.
- **Clean & Fast Interface**: A static frontend built with HTML, Vanilla JS, and Pico.css for a lightweight and responsive user experience.
- **Automated Updates**: A GitHub Actions workflow fetches new content every hour, ensuring the site is always up-to-date.
- **Resilient**: The system is designed to tolerate failures in individual RSS feeds without disrupting the overall operation.
- **Security First**: "Security by Design" architecture to minimize the attack surface.

## 🏛️ Architecture

The project uses a GitOps approach, separating the data collection process from content delivery.

1.  **Data Collection (GitHub Actions)**:
    - A scheduled workflow (`fetch_news.yml`) runs every hour.
    - The workflow executes a Python script (`app/fetcher.py`).
    - The script reads the news sources from `sources.json`, fetches the content from each RSS feed, classifies it using `keywords.json`, and generates a single static data file (`public/data.json`).
    - A `timestamp_added` is added to each item to track when it was added to the system.

2.  **Content Delivery (Static Hosting)**:
    - The `public/` directory contains a static website (HTML, CSS, JS).
    - When `data.json` is updated by the workflow, the commit triggers a deploy to a static hosting service (like GitHub Pages, Vercel, Netlify, etc.).
    - The JavaScript (`public/js/main.js`) on the client-side fetches `data.json` and dynamically renders the interface, preventing XSS attacks by treating all content as text (`.textContent`).

## 🛠️ Engineering Decisions

These are deliberate technical choices made to enhance the project's stability and performance.

#### Why Python 3.11 instead of 3.13?

The choice of Python 3.11 for the automation workflow is a conservative engineering decision focused on maximum reliability for a production environment (CI/CD).
* **Stability & Maturity**: Version 3.11 is battle-tested, with a mature ecosystem of libraries that have been extensively validated on it.
* **Ecosystem Compatibility**: It guarantees that our dependencies (like `feedparser`) and the execution environment (GitHub Actions runners) have stable, long-term support.
* **Risk vs. Reward**: The performance benefits of newer Python versions are negligible for this I/O-bound script, so we prioritize the proven stability of a slightly older, widely adopted version.

#### Why is the CSS embedded in the HTML?

Placing the CSS in a `<style>` block within the HTML is an **intentional performance optimization**.
* **Reduced HTTP Requests**: For a single-page application, this approach reduces the number of requests the browser must make from two (one for HTML, one for CSS) to just one.
* **Lower Latency**: This results in a faster "First Contentful Paint" (FCP), making the site feel significantly quicker for the user on their first visit.
* **Contextual Trade-off**: While external stylesheets are better for large, multi-page sites that can leverage caching, the embedded style approach provides the best performance for this project's specific scope.

## 🔒 Secure Software Development Lifecycle (SDLC)

Security was the top priority throughout this project's entire development lifecycle.

1.  **Design (Threat Modeling)**:
    - **Minimal Attack Surface**: Choosing a static architecture eliminates the need for a dynamic backend, database, or publicly exposed APIs, removing common attack vectors like SQL Injection, server-side RCE, etc.
    - **XSS Prevention**: The interface design specifies that all rendering of external content on the frontend must use `.textContent`, treating data as text and not as executable HTML.
    - **Dependencies**: The number of dependencies is minimal (`feedparser`) to reduce the risk of supply chain vulnerabilities.

2.  **Development (Secure Coding)**:
    - **Input Handling**: Although the site is static, the fetching script processes external data. Using the `feedparser` library helps to safely parse and normalize RSS data.
    - **Error Handling**: The `fetcher.py` script wraps the fetching of each source in a `try...except` block, ensuring that a malformed or unavailable feed does not crash the entire update process.
    - **Secrets Management**: The project does not require secrets (API keys, etc.), but if it did, they would be managed via GitHub Secrets and never hard-coded.

3.  **Testing (Security Testing)**:
    - **Dependency Scanning**: Tools like GitHub's Dependabot can be enabled to scan `requirements.txt` and alert on vulnerable dependencies.
    - **Static Analysis (SAST)**: Tools like CodeQL can be integrated into the CI/CD pipeline to analyze the Python and JavaScript code for insecure coding patterns.

4.  **Deploy (Secure Deployment)**:
    - **Principle of Least Privilege**: The GitHub Actions token (`GITHUB_TOKEN`) has limited permissions to the repository, just enough to commit the data file.
    - **Immutability**: The static nature of the site means that once deployed, it cannot be altered on the server, preventing most website defacement attacks.

## 🚀 How to Run Locally

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/zer0spin/infosec-digest.git](https://github.com/zer0spin/infosec-digest.git)
    cd infosec-digest
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the fetcher script:**
    ```bash
    python -m app.fetcher
    ```
    This will generate the `public/data.json` file.

5.  **Serve the website:**
    Use a local web server to serve the `public` directory.
    ```bash
    # If you have Python 3
    python -m http.server --directory public 8000
    ```
    Open `http://localhost:8000` in your browser.

---

## 📝 License

This project is licensed under the MIT License - See the [LICENSE](LICENSE) file for details.

---
*Created by [zer0spin](https://github.com/zer0spin)*