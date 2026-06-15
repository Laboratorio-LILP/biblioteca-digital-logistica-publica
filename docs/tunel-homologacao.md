# Túnel de homologação sem VPN

O comando `make tunnel` publica o portal local em uma URL `https://...devtunnels.ms`
protegida por login Microsoft. A equipe acessa o site de qualquer lugar, sem VPN
e sem instalar nada. Quando você encerra o túnel (Ctrl+C), o site sai do ar.

Usamos o serviço **Dev Tunnels**, da Microsoft — o mesmo dos "túneis de
desenvolvedor" do VS Code.

## Como publicar o portal (quem opera)

1. Suba o portal: `make up`
2. Na primeira vez, instale e faça login no serviço de túnel:

   ```sh
   brew install --cask devtunnel
   devtunnel user login
   ```

   **Importante:** entre com a conta Microsoft **corporativa** (a mesma do
   e-mail institucional). A liberação de acesso vale para quem está no mesmo
   "tenant" — o espaço da organização na Microsoft. Conta pessoal não serve.

3. Abra o túnel: `make tunnel`

O terminal mostra a URL pública na linha **"Connect via browser"**.
Envie essa URL para a equipe. O túnel fica ativo enquanto o terminal
estiver aberto.

## Como acessar (equipe)

Mensagem pronta para enviar:

> O ambiente de homologação da Biblioteca está disponível em: `<URL>`
>
> 1. Abra o link no navegador.
> 2. Entre com seu e-mail institucional (login Microsoft).
> 3. Se aparecer um aviso da Microsoft sobre "dev tunnel", confirme para continuar.
>
> O link só funciona enquanto o ambiente estiver publicado. Se não abrir,
> me avise.

## Como deixar no ar sem terminal aberto (serviço)

Para a equipe acessar a qualquer momento, instale o túnel como serviço do
macOS:

```sh
make tunnel-service
```

O serviço sobe junto com o login do usuário e reinicia sozinho se cair.
Não precisa de terminal aberto. Para ver a URL atual:

```sh
make tunnel-url
```

Para um diagnóstico rápido (serviços, conexões, portal local e URL):

```sh
make tunnel-status
```

`make tunnel-service` instala **dois** serviços que trabalham juntos:

- **O host** (`bdlp-tunnel`) — o processo que mantém o túnel aberto.
- **O watchdog** (`bdlp-tunnel-watchdog`) — checa a saúde do túnel a cada
  5 minutos e reinicia o host se ele ficar "vivo mas mudo" (ver abaixo).

Condições para o serviço funcionar:

- O Mac precisa estar **ligado e com o usuário logado** (Ajustes do Sistema →
  Tela de Bloqueio/Bateria: impedir suspensão se for servir por longos períodos).
- O stack precisa estar no ar (`make up`). Se não estiver, o serviço tenta
  de novo a cada 60 segundos até o portal responder.
- Logs: `~/Library/Logs/bdlp-tunnel.log` (host) e
  `~/Library/Logs/bdlp-tunnel-watchdog.log` (watchdog).

### Por que existe um watchdog

O launchd só reinicia o host quando o **processo morre**. Mas há uma falha
mais traiçoeira: o processo continua vivo, porém perde a conexão com o
servidor da Microsoft e não consegue se reautenticar (token expirado, queda
de rede). O site fica fora do ar, mas o launchd acha que está tudo bem —
porque o processo existe.

O sinal de saúde correto não é "o processo existe", e sim "o túnel tem
conexão de host". O watchdog verifica exatamente isso e, se as conexões
caírem a zero, reinicia o host — que sobe limpo e se reautentica.

> **Atenção a um falso positivo:** abrir a URL sem login devolve um
> redirecionamento (HTTP 302) para a tela da Microsoft mesmo com o túnel
> quebrado. Logo, "a URL respondeu" **não** significa "o site está no ar".
> Use `make tunnel-status` para o veredito real.

## Como tirar do ar

- **Serviço:** `make tunnel-service-off` — remove o host e o watchdog e
  derruba o acesso.
- **Terminal (`make tunnel`):** pressione **Ctrl+C**.

Nos dois casos o acesso externo morre na hora. O portal continua rodando
localmente em `http://localhost:8000`.

## Por que é seguro

- **O portal só escuta em `127.0.0.1`.** Ninguém alcança o container pela
  rede; o túnel é a única porta de entrada.
- **Sem acesso anônimo.** O túnel exige login Microsoft e só aceita contas
  do tenant corporativo. URL vazada não dá acesso a estranhos.
- **HTTPS de ponta a ponta.** A Microsoft emite o certificado; nada trafega
  em texto claro.
- **`DEBUG=false` no `.env`.** Erros não expõem stack trace, e o site roda
  com os mesmos headers de segurança (CSP etc.) da produção.
- **Hosts validados.** O Django rejeita requisições cujo `Host` não seja
  `localhost` ou `*.devtunnels.ms` (HTTP 400).

## Problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| Colega vê "acesso negado" após o login | Conta fora do tenant (ex.: e-mail pessoal) | Pedir que entre com o e-mail institucional |
| Erro 400 ao abrir a URL | `ALLOWED_HOSTS` sem `.devtunnels.ms` | Conferir o `.env` da raiz e rodar `make up` |
| "portal não responde" ao rodar `make tunnel` | Stack Docker parado | Rodar `make up` antes |
| Túnel sumiu depois de dias parado | O serviço apaga túneis após ~4 dias sem uso | Rodar `make tunnel` de novo — o script recria e gera **URL nova** (reenvie à equipe) |
| Equipe sem acesso, mas `make tunnel-status` mostra `Host connections: 0` | Host zumbi (processo vivo, sem conexão) | O watchdog reinicia em até 5 min; para resolver na hora: `launchctl kickstart -k gui/$(id -u)/br.gov.sp.lilp.bdlp-tunnel` |
| Watchdog reinicia em loop (log com "FALHA no kickstart" ou Unauthorized) | Login Microsoft expirou de vez | `devtunnel user login` (conta institucional) e depois `make tunnel-service` |
| Site lento ou bloqueado no meio do dia | Limite de banda do plano gratuito | Usar para homologar páginas; evitar download em massa de PDFs |

## Quando voltar ao modo de desenvolvimento

O túnel usa o mesmo stack local. Para depurar com páginas de erro detalhadas:

1. Encerre o túnel (Ctrl+C) — nunca depure com o site exposto.
2. No `.env` da raiz, troque `DJANGO_DEBUG=false` por `true`.
3. Rode `make up`.

Antes de publicar de novo, volte `DJANGO_DEBUG=false`.
