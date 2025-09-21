[Read in English (en)](README.md)

# InfoSec Digest

O **InfoSec Digest** é um agregador de notícias e podcasts de cibersegurança moderno, seguro e de alto desempenho. O projeto foi construído com uma arquitetura GitOps desacoplada, servindo conteúdo de forma estática para máxima segurança e velocidade, com atualizações totalmente automatizadas.

## ✨ Features

- **Conteúdo Centralizado**: Agrega as últimas notícias e episódios de podcasts das fontes mais relevantes de cibersegurança.
- **Interface Limpa e Rápida**: Frontend estático construído com HTML, Vanilla JS e Pico.css para uma experiência de usuário leve e responsiva.
- **Atualizações Automáticas**: Um workflow do GitHub Actions busca novo conteúdo a cada hora, garantindo que o site esteja sempre atualizado.
- **Resiliência**: O sistema é projetado para tolerar falhas em feeds RSS individuais sem interromper a operação geral.
- **Segurança em Primeiro Lugar**: Arquitetura "Security by Design" para minimizar a superfície de ataque.

## 🏛️ Arquitetura

O projeto utiliza uma abordagem GitOps, separando o processo de coleta de dados da entrega do conteúdo.

1.  **Coleta de Dados (GitHub Actions)**:
    - Um workflow agendado (`fetch_news.yml`) é executado a cada hora.
    - O workflow executa um script Python (`app/fetcher.py`).
    - O script lê as fontes de notícias do arquivo `sources.json`, busca o conteúdo de cada feed RSS, o classifica usando `keywords.json` e gera um único arquivo de dados estático (`public/data.json`).
    - Um `timestamp_added` é adicionado a cada item para rastrear quando ele foi adicionado ao sistema.

2.  **Entrega de Conteúdo (Static Hosting)**:
    - O diretório `public/` contém um site estático (HTML, CSS, JS).
    - Quando o `data.json` é atualizado pelo workflow, o commit aciona um deploy para um serviço de hospedagem estática (como GitHub Pages, Vercel, Netlify, etc.).
    - O JavaScript (`public/js/main.js`) no lado do cliente faz o fetch do `data.json` e renderiza dinamicamente a interface, prevenindo ataques XSS ao tratar todo o conteúdo como texto (`.textContent`).

## 🛠️ Decisões de Engenharia

Estas são escolhas técnicas deliberadas, feitas para aprimorar a estabilidade e o desempenho do projeto.

#### Por que Python 3.11 e não 3.13?

A escolha do Python 3.11 no workflow de automação é uma decisão de engenharia conservadora, focada na **máxima confiabilidade** para um ambiente de produção (CI/CD).
* **Estabilidade e Maturidade**: A versão 3.11 é "battle-tested", com um ecossistema maduro de bibliotecas que foram extensivamente validadas nela.
* **Compatibilidade do Ecossistema**: Garante que nossas dependências (como `feedparser`) e o ambiente de execução (runners do GitHub Actions) tenham suporte estável e de longo prazo.
* **Risco vs. Recompensa**: Os benefícios de performance de versões mais novas são negligenciáveis para este script, então priorizamos a estabilidade comprovada de uma versão um pouco mais antiga e amplamente adotada.

#### Por que o CSS está embutido no HTML?

Colocar o CSS em um bloco `<style>` dentro do HTML, em vez de um arquivo `.css` externo, é uma **otimização de performance intencional**.
* **Redução de Requisições HTTP**: Para um site de página única, essa abordagem reduz o número de requisições que o navegador precisa fazer de duas (uma para o HTML, outra para o CSS) para apenas uma.
* **Menor Latência**: Isso resulta em uma "Primeira Renderização de Conteúdo" (FCP) mais rápida, fazendo o site parecer significativamente mais ágil para o usuário na primeira visita.
* **Trade-off Contextual**: Enquanto folhas de estilo externas são melhores para sites grandes com múltiplas páginas (que se beneficiam do cache), a abordagem de CSS embutido oferece a melhor performance para o escopo específico deste projeto.

## 🔒 Secure Software Development Lifecycle (SDLC)

A segurança foi a principal prioridade durante todo o ciclo de vida de desenvolvimento deste projeto.

1.  **Design (Threat Modeling)**:
    - **Superfície de Ataque Mínima**: A escolha de uma arquitetura estática elimina a necessidade de um backend dinâmico, banco de dados ou APIs expostas ao público, removendo vetores de ataque comuns como SQL Injection, RCE no servidor, etc.
    - **Prevenção de XSS**: O design da interface especifica que toda a renderização de conteúdo de fontes externas no frontend deve usar `.textContent`, tratando os dados como texto e não como HTML executável.
    - **Dependências**: O número de dependências é mínimo (`feedparser`) para reduzir o risco de vulnerabilidades na cadeia de suprimentos.

2.  **Desenvolvimento (Secure Coding)**:
    - **Validação de Entrada**: Embora o site seja estático, o script de fetching processa dados externos. O uso da biblioteca `feedparser` ajuda a normalizar e analisar os dados de RSS de forma segura.
    - **Tratamento de Erros**: O script `fetcher.py` encapsula a busca de cada fonte em um bloco `try...except`, garantindo que um feed malformado ou indisponível não derrube todo o processo de atualização.
    - **Gerenciamento de Segredos**: O projeto não requer segredos (chaves de API, etc.), mas se precisasse, eles seriam gerenciados via GitHub Secrets e nunca hard-coded.

3.  **Testes (Security Testing)**:
    - **Scanning de Dependências**: Ferramentas como o Dependabot do GitHub podem ser ativadas para escanear `requirements.txt` e alertar sobre dependências vulneráveis.
    - **Análise Estática (SAST)**: Ferramentas como CodeQL podem ser integradas ao pipeline de CI/CD para analisar o código Python e JavaScript em busca de padrões de codificação inseguros.

4.  **Deploy (Secure Deployment)**:
    - **Princípio do Menor Privilégio**: O token do GitHub Actions (`GITHUB_TOKEN`) tem permissões limitadas ao repositório, apenas o suficiente para fazer commit do arquivo de dados.
    - **Imutabilidade**: A natureza estática do site significa que, uma vez implantado, ele não pode ser alterado no servidor, prevenindo a maioria dos ataques de desfiguração de sites.

## 🚀 Como Executar Localmente

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/zer0spin/infosec-digest.git](https://github.com/zer0spin/infosec-digest.git)
    cd infosec-digest
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Execute o script de coleta:**
    ```bash
    python -m app.fetcher
    ```
    Isso irá gerar o arquivo `public/data.json`.

5.  **Visualize o site:**
    Use um servidor web local para servir o diretório `public`.
    ```bash
    # Se você tiver Python 3
    python -m http.server --directory public 8000
    ```
    Abra `http://localhost:8000` em seu navegador.

---
*Criado por [zer0spin](https://github.com/zer0spin)*