# RotaLag

Monitor leve de qualidade de rede e de rotas para jogos online. Projeto de TCC.

O RotaLag roda em segundo plano, mede a conexão por vários dias e mostra em que horários ela fica mais lenta ou perde mais pacotes. As próximas fases adicionam detecção de jogos, verificação dos servidores, histórico de rotas, alertas e sugestões de solução.

## Estado atual: fase 1 (linha de base)

- Ping periódico para 8.8.8.8, 1.1.1.1, 9.9.9.9 e o gateway da sua casa (roteador/modem).
- Grava latência média, mínima, máxima, jitter e perda de cada rodada num banco SQLite local.
- Relatório com o perfil da conexão por hora do dia e os piores horários.
- Ícone na bandeja (verde, amarelo ou vermelho), opcional.
- Não precisa de administrador e não depende de bibliotecas externas para o núcleo.

## Como usar (Windows)

Precisa do Python 3.11 ou mais novo.

```powershell
git clone https://github.com/Heliomuniz/rotalag.git
cd rotalag
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[bandeja]"

rotalag testar        # uma rodada rápida em cada alvo, sem gravar
rotalag rodar         # começa a monitorar (ícone na bandeja)
rotalag relatorio     # perfil por hora dos últimos 7 dias
```

Sem o ícone: `rotalag rodar --sem-bandeja` (Ctrl+C para sair).

## Onde ficam os dados

- Windows: `%LOCALAPPDATA%\RotaLag\dados.db`
- Linux: `~/.local/share/RotaLag/dados.db`

Para mudar a configuração, crie `config.toml` nessa mesma pasta:

```toml
intervalo_s = 30          # segundos entre rodadas para cada alvo
pacotes = 10              # pacotes por rodada
timeout_ms = 1000
alvos = ["8.8.8.8", "1.1.1.1", "9.9.9.9"]
monitorar_gateway = true
```

## Testes

```bash
pip install -e ".[dev]"
pytest
```

## Estrutura

| Arquivo | Papel |
| --- | --- |
| `src/rotalag/ping.py` | Executa o `ping` do sistema e calcula as estatísticas |
| `src/rotalag/gateway.py` | Descobre o gateway padrão |
| `src/rotalag/storage.py` | Banco SQLite (tabelas `alvos` e `amostras_ping`) |
| `src/rotalag/collector.py` | Uma thread por alvo, rodando a cada `intervalo_s` |
| `src/rotalag/report.py` | Perfil por hora do dia e piores horários |
| `src/rotalag/tray.py` | Ícone na bandeja |
| `src/rotalag/__main__.py` | Linha de comando |
