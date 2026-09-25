# 📖 Manual de Uso — Anonimizador de PDF

Guia completo, do zero até o PDF anonimizado, com todos os recursos explicados.

---

## 📌 Índice

1. [O que é o app](#1-o-que-é-o-app)
2. [Acessando o app](#2-acessando-o-app)
3. [Tela principal (visão geral)](#3-tela-principal-visão-geral)
4. [Passo a passo básico](#4-passo-a-passo-básico)
5. [Entendendo as duas formas de anonimizar](#5-entendendo-as-duas-formas-de-anonimizar)
6. [Usando substituição simples](#6-usando-substituição-simples)
7. [Usando Regex (padrões automáticos)](#7-usando-regex-padrões-automáticos)
8. [Configurações avançadas](#8-configurações-avançadas)
9. [Exemplos práticos prontos](#9-exemplos-práticos-prontos)
10. [Perguntas frequentes](#10-perguntas-frequentes)
11. [Solução de problemas](#11-solução-de-problemas)

---

## 1. O que é o app

O **Anonimizador de PDF** é uma ferramenta web que:

- ✅ Carrega um PDF (qualquer quantidade de páginas)
- ✅ Substitui **em massa** palavras, nomes, CPFs, e-mails, telefones, etc.
- ✅ Ou cobre esses dados com **tarja preta** (redaction)
- ✅ Devolve o arquivo alterado para download

Tudo roda **no navegador**, sem login, sem banco de dados e sem enviar seus arquivos para servidores de terceiros.

---

## 2. Acessando o app

Abra no navegador o endereço do seu Streamlit Cloud. Ele será algo como:

```
https://SEU-USUARIO-anonimizador-pdf.streamlit.app
```

> 💤 **Se o app estiver "dormindo"** (acontece após dias sem uso no plano grátis), basta abrir a URL que ele acorda em ~30 segundos.

---

## 3. Tela principal (visão geral)

A tela é dividida em 3 áreas:

```
┌─────────────────────────────────────────────────────────────┐
│  🔒 Anonimizador de PDF                                     │
│  ─────────────────────────────────────────────────────      │
│                                                             │
│  📄 Carregue o PDF         ← área de upload                 │
│  [ Escolher arquivo ]                                       │
│                                                             │
│  📝 Regras de substituição ← onde você define o que trocar  │
│  Localizar | Substituir por                                 │
│  [ ______ ] [ ______ ] 🗑️                                  │
│  [ ➕ Adicionar regra ]                                     │
│                                                             │
│  [ 🚀 Anonimizar PDF ]     ← botão para processar           │
│                                                             │
│  [ ⬇️ Baixar PDF anonimizado ] ← aparece após processar     │
└─────────────────────────────────────────────────────────────┘

┌─── Menu lateral (⚙️ Configurações) ───┐
│  Modo de anonimização                 │
│  Regex                                │
│  Ajustes de fonte                     │
│  Exemplos de Regex                    │
└───────────────────────────────────────┘
```

---

## 4. Passo a passo básico

### 🔹 Passo 1 — Carregar o PDF

1. Na área **📄 Carregue o PDF**, clique em **Browse files**
2. Selecione o arquivo `.pdf` do seu computador
3. Aguarde — o nome do arquivo aparece confirmando o upload

> ⚠️ Só aceita arquivos com extensão `.pdf`

---

### 🔹 Passo 2 — Adicionar as regras de substituição

1. Na seção **📝 Regras de substituição**, você verá duas colunas:
   - **Localizar** → o que deve ser encontrado
   - **Substituir por** → o que vai entrar no lugar

2. No primeiro campo, digite o texto original. Exemplo:
   ```
   111.111.111-11
   ```

3. No segundo campo, digite o substituto:
   ```
   000.000.000-00
   ```

4. Para adicionar mais regras, clique em **➕ Adicionar regra** e repita.

5. Para remover uma regra, clique no ícone **🗑️** ao lado dela.

---

### 🔹 Passo 3 — (Opcional) Ajustar configurações

No menu lateral esquerdo, veja a seção [Configurações avançadas](#8-configurações-avançadas) mais abaixo neste manual.

---

### 🔹 Passo 4 — Processar

1. Clique em **🚀 Anonimizar PDF**
2. Uma barra de progresso mostra o andamento página a página
3. Ao final, aparece a mensagem:
   ```
   ✅ Concluído! N ocorrência(s) processada(s).
   ```

---

### 🔹 Passo 5 — Baixar o arquivo

1. Clique em **⬇️ Baixar PDF anonimizado**
2. O arquivo será salvo como `anonimizado.pdf`
3. Abra e confira o resultado!

---

## 5. Entendendo as duas formas de anonimizar

No menu lateral, em **Modo de anonimização**, você escolhe entre:

### 🅰️ Substituir texto

Troca o texto antigo por um novo, mantendo o mesmo lugar.

| Antes | Depois |
|---|---|
| `JOSE MARIA SILVA` | `CARLOS PATRICK` |
| `111.111.111-11` | `000.000.000-00` |

✅ **Quando usar:** quando você quer manter o documento legível, apenas trocando informações.

---

### 🅱️ Tarjar (tarja preta)

Cobre o texto com um retângulo preto. O texto original é **removido do PDF** (não dá para copiar depois).

| Antes | Depois |
|---|---|
| `JOSE MARIA SILVA` | ████████████████ |

✅ **Quando usar:** quando você quer **ocultar completamente** o dado sensível, sem que ninguém possa recuperá-lo.

> 💡 **Importante:** o app faz redaction **de verdade** — o texto é removido do conteúdo do PDF, não apenas coberto com um retângulo. Isso é o padrão correto de segurança.

---

## 6. Usando substituição simples

**Cenário:** você tem 100 páginas de contratos com CPFs e nomes a trocar.

1. Modo: **Substituir texto**
2. Regras:

| Localizar | Substituir por |
|---|---|
| `111.111.111-11` | `000.000.000-00` |
| `JOSE MARIA` | `CARLOS PATRICK` |
| `jose.maria@email.com` | `anonimo@email.com` |

3. **Regex desmarcado** (deixe a opção lateral desativada)
4. Clique em **🚀 Anonimizar PDF**
5. Baixe o resultado

> ⚠️ A busca sem Regex é **case-sensitive** quando o texto contém diferença de maiúsculas/minúsculas. Se precisar pegar variações (`jose maria`, `JOSE MARIA`, `Jose Maria`), use Regex.

---

## 7. Usando Regex (padrões automáticos)

**Cenário:** você quer trocar **todos os CPFs** de um PDF, sem saber quais são.

1. No menu lateral, marque ✅ **Usar expressões regulares (Regex)**
2. Na regra, coloque o padrão:

| Localizar | Substituir por |
|---|---|
| `\d{3}\.\d{3}\.\d{3}-\d{2}` | `000.000.000-00` |

3. Pronto — o app encontra todos os CPFs e substitui.

### 🔤 Regex mais usados (prontos para colar)

| O que buscar | Padrão Regex |
|---|---|
| **CPF** | `\d{3}\.\d{3}\.\d{3}-\d{2}` |
| **CPF (sem pontos)** | `\d{11}` |
| **CNPJ** | `\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}` |
| **E-mail** | `[\w\.-]+@[\w\.-]+\.\w+` |
| **Telefone (fixo/celular)** | `\(\d{2}\)\s?\d{4,5}-\d{4}` |
| **CEP** | `\d{5}-\d{3}` |
| **Data (dd/mm/aaaa)** | `\d{2}/\d{2}/\d{4}` |
| **Nomes completos (aprox.)** | `[A-Z][a-z]+(\s[A-Z][a-z]+)+` |

> 💡 **Dica:** com Regex ativo, você pode marcar **Diferenciar maiúsculas/minúsculas** se quiser busca exata — deixe desmarcado para pegar variações.

---

## 8. Configurações avançadas

No menu lateral esquerdo:

### 🎛️ Modo de anonimização
Já explicado na seção 5.

### 🔣 Usar expressões regulares (Regex)
Ativa o modo Regex. Já explicado na seção 7.

### 🔡 Diferenciar maiúsculas/minúsculas
- **Desmarcado** (padrão): `jose` encontra `JOSE`, `Jose`, `jose`
- **Marcado:** busca exata, respeitando maiúsculas/minúsculas

### 🔠 Ajustar tamanho da fonte automaticamente
- **Marcado** (recomendado): o app tenta manter o tamanho original do texto
- **Desmarcado:** você define manualmente no slider abaixo

### 📏 Tamanho da fonte manual
Slider de 6 a 24 — só ativo quando **"Ajustar automaticamente"** está desmarcado.

### ↔️ Expandir caixa de texto
- **Marcado** (recomendado): permite substituições maiores que o texto original (ex: `JOSE` → `CARLOS PATRICK`)
- **Desmarcado:** mantém exatamente a mesma largura, podendo cortar textos longos

---

## 9. Exemplos práticos prontos

### 🔸 Exemplo 1 — Anonimizar um contrato

| Localizar | Substituir por |
|---|---|
| `111.111.111-11` | `000.000.000-00` |
| `JOSE MARIA SILVA` | `CARLOS PATRICK SOUZA` |
| `Rua das Flores, 123` | `Rua Anônima, 000` |
| `jose.silva@email.com` | `anonimo@email.com` |

Modo: **Substituir texto**. Regex: **desmarcado**.

---

### 🔸 Exemplo 2 — Tarjar todos os CPFs de um lote

| Localizar | Substituir por |
|---|---|
| `\d{3}\.\d{3}\.\d{3}-\d{2}` | *(deixe em branco)* |

Modo: **Tarjar (tarja preta)**. Regex: **marcado**.

---

### 🔸 Exemplo 3 — Limpar folha de pagamento

| Localizar | Substituir por |
|---|---|
| `[\w\.-]+@[\w\.-]+\.\w+` | `anonimo@empresa.com` |
| `\(\d{2}\)\s?\d{4,5}-\d{4}` | `(00) 00000-0000` |
| `\d{3}\.\d{3}\.\d{3}-\d{2}` | `000.000.000-00` |

Modo: **Substituir texto**. Regex: **marcado**.

---

### 🔸 Exemplo 4 — Múltiplos nomes específicos

Adicione **uma regra por nome**:

| Localizar | Substituir por |
|---|---|
| `JOSE MARIA` | `PESSOA 001` |
| `MARIA JOSE` | `PESSOA 002` |
| `CARLOS EDUARDO` | `PESSOA 003` |
| `ANA PAULA` | `PESSOA 004` |

Modo: **Substituir texto**. Regex: **desmarcado**.

---

## 10. Perguntas frequentes

### ❓ O texto antigo é realmente apagado?
✅ **Sim.** O app usa `apply_redactions()` do PyMuPDF, que remove o texto do fluxo de conteúdo do PDF. Diferente de "só pintar por cima", aqui o conteúdo é **destruído**.

### ❓ Meus arquivos ficam salvos em algum servidor?
❌ **Não.** Todo processamento ocorre em memória. Nada é armazenado em disco ou banco de dados.

### ❓ Funciona em PDF digitalizado (só imagem)?
❌ **Não diretamente.** PDFs que são apenas imagens escaneadas não têm texto pesquisável. Nesse caso, é preciso rodar **OCR** primeiro (ex: Adobe Acrobat, Tesseract).

### ❓ Quantas páginas suporta?
✅ Testado com **100+ páginas** sem problema. O PyMuPDF é rápido (C nativo).

### ❓ Posso usar acentos e caracteres especiais?
⚠️ **Parcialmente.** A fonte padrão `Helvetica` cobre bem o português (á, ã, ç, é...). Emojis, japonês, árabe e cirílico **não** funcionam com a fonte padrão.

### ❓ O app guarda histórico das minhas buscas?
❌ **Não.** Cada visita é independente. Ao recarregar a página, tudo é zerado.

### ❓ Preciso criar conta?
❌ **Não.** Sem login, sem cadastro.

---

## 11. Solução de problemas

| Problema | Causa provável | Solução |
|---|---|---|
| **Não encontrou a palavra** | Diferença de maiúsculas/minúsculas | Use Regex com case-insensitive |
| **Texto saiu cortado** | "Expandir caixa" desmarcado | Marque a opção lateral |
| **Fonte muito grande/pequena** | Auto-ajuste errado | Desmarque auto, use slider manual |
| **Acentos aparecem como símbolos** | Fonte não cobre o caractere | Me avise — é preciso registrar fonte customizada |
| **PDF está em branco após processar** | Regras com `find` vazio foram incluídas | Verifique se todas as regras têm texto |
| **Erro `ModuleNotFoundError: fitz`** | `requirements.txt` ausente ou com nome errado | Renomear para `requirements.txt` (com "i") e reiniciar |
| **App "dormiu"** | Plano grátis inativo | Reabra a URL, ele acorda em ~30s |
| **Muito lento em PDF gigante** | Muitas regras × muitas páginas | Divida o PDF e processe em partes |

---

## 🎓 Fluxo resumido (cola rápida)

```
1. Carregar PDF
2. Adicionar regras (Localizar → Substituir)
3. Escolher modo (Substituir | Tarjar)
4. (Opcional) Ativar Regex
5. Clicar em 🚀 Anonimizar PDF
6. Clicar em ⬇️ Baixar PDF anonimizado
```

---

## 💡 Boas práticas

1. **Sempre teste em um PDF pequeno primeiro** (2-3 páginas) antes de rodar num lote grande
2. **Guarde o PDF original** — o app devolve outro arquivo, mas é bom ter backup
3. **Confira o resultado** abrindo o PDF e usando Ctrl+F para buscar o dado sensível — se não achar, funcionou
4. **Para dados realmente sensíveis**, use o modo **Tarjar** — ele é mais seguro que a substituição
5. **Use Regex** quando os dados têm padrão fixo (CPF, e-mail, telefone) — muito mais rápido que regra por regra

---

Pronto! Com este manual você consegue usar 100% do app. Se quiser, posso gerar também:

- 📄 Uma versão em PDF do manual
- 🎬 Um passo a passo com imagens (posso descrever as telas)
- 🌐 Adicionar uma página de **Ajuda** dentro do próprio app (link no topo)

É só dizer! 🚀
