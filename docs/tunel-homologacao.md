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

## Como tirar do ar

Pressione **Ctrl+C** no terminal onde o túnel roda. O acesso externo morre
na hora. O portal continua rodando localmente em `http://localhost:8000`.

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
| Site lento ou bloqueado no meio do dia | Limite de banda do plano gratuito | Usar para homologar páginas; evitar download em massa de PDFs |

## Quando voltar ao modo de desenvolvimento

O túnel usa o mesmo stack local. Para depurar com páginas de erro detalhadas:

1. Encerre o túnel (Ctrl+C) — nunca depure com o site exposto.
2. No `.env` da raiz, troque `DJANGO_DEBUG=false` por `true`.
3. Rode `make up`.

Antes de publicar de novo, volte `DJANGO_DEBUG=false`.
