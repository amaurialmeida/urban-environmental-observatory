# Urban Environmental Observatory

Sistema exploratório de comparação socioambiental urbana.

O MVP compara duas cidades usando a API oficial do Numbeo como camada de **percepção dos usuários**. A proposta evolui em cinco versões:

1. **MVP:** Numbeo + comparação visual entre cidades.
2. **Versão 2:** qualidade do ar medida e clima com OpenAQ/Open-Meteo.
3. **Versão 3:** saneamento, água, esgoto, resíduos e infraestrutura pública.
4. **Versão 4:** séries históricas, mapa, índice multicritério e análise de sensibilidade.
5. **Versão 5:** alertas ambientais, relatórios automáticos e modelos de Machine Learning.

## Execução local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export NUMBEO_API_KEY="sua-chave"
streamlit run app.py
```

## Streamlit Community Cloud

Em **Settings → Secrets**, adicione:

```toml
NUMBEO_API_KEY = "sua-chave"
```

Nunca publique a chave no GitHub.

## Escopo metodológico

- O Numbeo é usado como percepção urbana, não como medição laboratorial.
- O índice de poluição original tem interpretação própria do Numbeo: menor é melhor.
- Os indicadores ambientais exibidos no radar são transformados para uma escala de 0 a 100 orientada para melhor percepção.
- A quantidade de contribuintes e a data informada pela API devem acompanhar cada resultado.
- A ausência de dados não deve ser interpretada como boa condição ambiental.

## Licença e atribuição

Antes da publicação pública, confirme que o plano/licença da API do Numbeo cobre o uso em uma aplicação pública de portfólio. Consulte os [termos de uso do Numbeo](https://www.numbeo.com/common/terms_of_use.jsp) e mantenha a atribuição para `numbeo.com`.

## Visão de dados

```text
Percepção do usuário (Numbeo)
        +
Infraestrutura urbana (fontes públicas)
        +
Indicadores ambientais medidos (sensores/satélite)
        =
Comparação socioambiental exploratória
```

Este projeto não produz um ranking absoluto de cidades. Ele apresenta sinais, diferenças, incertezas e hipóteses para investigação ambiental.
