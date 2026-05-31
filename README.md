# Mission Control AI - ConnectSat

## Integrante
- Kayo Henderson
- RM: 570706
- Turma: 1CCPK

## Modalidade
- Individual
## O que o projeto faz
Sistema de monitoramento de satélite ConnectSat com telemetria simulada, detecção de anomalias por regras Python e análise contextual via IA generativa.
O foco é transformar sinais técnicos em resposta operacional e impacto terrestre para inclusão digital.

## Persona atendida
Operador NOC de conectividade rural, que precisa priorizar continuidade de internet para escolas, telemedicina e serviços essenciais.

## Tecnologias utilizadas
- Python 3.10+
- Ollama Cloud API (modelo padrão: `gpt-oss:120b`)
- `ollama==0.6.2`
- `python-dotenv==1.2.2`
- `rich==15.0.0`
- `prompt-toolkit==3.0.52`
- `pyfiglet==1.0.4`

## Como executar
1. Clone o repositório.
2. Crie e ative um ambiente virtual.
3. Instale as dependências:
   - `pip install -r requirements.txt`
4. Crie um arquivo `.env` na raiz com:
   - `OLLAMA_API_KEY=sua_chave`
   - opcional: `OLLAMA_HOST=https://ollama.com`
   - opcional: `OLLAMA_MODEL=gpt-oss:120b`
5. Execute:
   - `python main.py`

## Comandos da CLI
- `ajuda` ou `/help`
- `status` ou `/status`
- `telemetria`
- `alertas`
- `cenario <normal|latencia|critico|apagao>`
- `resposta`
- `impacto`
- `analisar <pergunta>`
- `sair` ou `/exit`

## Demonstração
- Adicionar prints reais em `assets/`:
  - `assets/screenshot_normal.png`
  - `assets/screenshot_alerta.png`

## System Prompt
O prompt está em: `prompts/system_prompt.md`

## Cenários de teste
1. Operação normal (`cenario normal`)
2. Latência elevada (`cenario latencia`)
3. Situação crítica (`cenario critico`)
4. Quase apagão (`cenario apagao`)

## Limitações conhecidas
- Telemetria ainda é simulada (sem ingestão de stream real).
- Não há persistência de histórico em banco.
- Não há suíte automatizada de testes.

## Proposta de valor / modelo de negócio
1. Quem se beneficia na Terra:
   - Comunidades rurais, escolas e unidades de saúde conectadas por satélite.
2. Quem paga pela operação:
   - Operadoras de telecom, governos locais e programas de inclusão digital.
3. Qual problema econômico/social resolve:
   - Reduz indisponibilidade de comunicação em áreas sem infraestrutura de fibra.
4. Métricas de sucesso:
   - Menor tempo de resposta a incidentes.
   - Redução de perda de pacotes em eventos críticos.
   - Melhoria de continuidade para serviços essenciais.

## Vídeo de demonstração
- Adicionar link YouTube não listado aqui após gravar.

