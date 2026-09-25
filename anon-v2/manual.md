# 📖 Manual de Uso — Anonimizador de PDF

Guia completo, do zero até o PDF anonimizado.

---

## 1. O que é o app

O **Anonimizador de PDF** é uma ferramenta web que:

- Carrega um PDF (qualquer quantidade de páginas)
- Substitui **em massa** palavras, nomes, CPFs, e-mails, telefones, etc.
- Ou cobre esses dados com **tarja preta** (redaction real)
- **Detecta automaticamente** dados sensíveis no PDF
- Devolve o arquivo alterado para download

Tudo roda **no navegador**, sem login, sem banco de dados.

---

## 2. Tela principal (visão geral)

- **Menu lateral (Configurações):** modo, regex, fonte
- **Aba Anonimizador:** upload, scanner, regras, processar
- **Aba Manual:** este manual

---

## 3. Passo a passo básico

### Passo 1 — Carregar o PDF

Na área **Carregue o PDF**, clique em **Browse files** e selecione um arquivo `.pdf`.

### Passo 2 — (Opcional) Escanear dados sensíveis

Na seção **Scanner de dados sensíveis**, clique em:

> **Escanear PDF em busca de dados sensíveis**

O app varre **todas as páginas** procurando por:

| Tipo | Exemplo |
|---|---|
| CPF | 111.111.111-00 |
| CNPJ | 11.111.111/0001-11 |
| CEP | 01310-100 |
| E-mail | jose@email.com |
| Telefone | (11) 98765-4321 |
| Cartão de crédito | 4111 1111 1111 1111 |
| Data | 01/01/2024 |
| Valor R$ | R$ 1.234,56 |
| Placa de veículo | ABC-1234 |
| Chave PIX aleatória | 12345678-1234-1234-1234-123456789012 |

Os resultados aparecem em uma **tabela interativa** com checkboxes. Marque o que deseja anonimizar (pode marcar todos), edite a coluna **Substituir por** se quiser, e clique em:

> **Adicionar selecionados como regras**

Os valores selecionados viram **regras normais** — você pode editá-las ou removê-las antes de processar.

> **Dica:** use as regras vindas do scanner com **Regex DESATIVADO** para máxima precisão.

### Passo 3 — Adicionar regras manualmente

Na seção **Regras de substituição**:

- **Localizar** → o que deve ser encontrado
- **Substituir por** → o que vai no lugar

Clique em **Adicionar regra** para incluir mais, e no ícone de lixeira para remover.

### Passo 4 — Processar

Clique em **Anonimizar PDF**. Uma barra de progresso mostra o andamento página a página.

### Passo 5 — Baixar

Clique em **Baixar PDF anonimizado**. O arquivo é salvo como `anonimizado.pdf`.

---

## 4. As duas formas de anonimizar

No menu lateral, em **Modo de anonimização**:

### Substituir texto

Troca o texto antigo por um novo no mesmo lugar.

| Antes | Depois |
|---|---|
| JOSE MARIA SILVA | CARLOS PATRICK |
| 111.111.111-11 | 000.000.000-00 |

**Quando usar:** quando você quer manter o documento legível, apenas trocando informações.

### Tarjar (tarja preta)

Cobre o texto com um retângulo preto. O texto original é **removido** do conteúdo do PDF.

**Quando usar:** quando você quer **ocultar completamente** o dado.

> O app faz redaction **de verdade** — usa `apply_redactions()` do PyMuPDF, que destrói o texto original do fluxo de conteúdo.

---

## 5. Scanner automático de dados sensíveis

Funcionalidade mais poderosa do app. Use quando você **não sabe** quais dados sensíveis existem no PDF.

### Como funciona

1. Carregue o PDF
2. Clique em **Escanear PDF em busca de dados sensíveis**
3. O app percorre **todas as páginas** aplicando 10 padrões Regex prontos
4. Aparece uma tabela com **tudo que encontrou**, agrupado por tipo + valor
5. Você marca com checkbox só o que quer anonimizar
6. Clica em **Adicionar selecionados como regras**
7. Revisa as regras (pode editar/remover)
8. Clica em **Anonimizar PDF**

### Vantagens

- Você **não precisa saber** de antemão o CPF que está na página 47
- Você **não precisa lembrar** dos formatos de e-mail, telefone, etc.
- Você escolhe **caso a caso** o que anonimizar

### Limitações honestas

- Regex pega o que **tem formato fixo** (CPF, e-mail, etc.)
- **Não pega** nomes de pessoas, endereços por extenso, nomes de empresas
- Pode haver **falsos positivos** — por isso a tabela tem checkboxes
- Para nomes específicos, use regras manuais (ex: JOSE MARIA → CARLOS PATRICK)

---

## 6. Regex úteis (para colar nas regras)

| O que buscar | Padrão Regex |
|---|---|
| CPF | `\d{3}\.\d{3}\.\d{3}-\d{2}` |
| CNPJ | `\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}` |
| E-mail | `[\w\.-]+@[\w\.-]+\.\w+` |
| Telefone (fixo/celular) | `\(\d{2}\)\s?\d{4,5}-\d{4}` |
| CEP | `\d{5}-\d{3}` |
| Data (dd/mm/aaaa) | `\d{2}/\d{2}/\d{4}` |
| Nomes completos (aprox.) | `[A-Z][a-z]+(\s[A-Z][a-z]+)+` |

---

## 7. Configurações avançadas (menu lateral)

### Modo de anonimização

- **Substituir texto** (padrão)
- **Tarjar (tarja preta)**

### Usar expressões regulares (Regex)

Ativa o modo Regex. Necessário para padrões como `\d{3}\.\d{3}\.\d{3}-\d{2}`.

### Diferenciar maiúsculas/minúsculas

- **Desmarcado** (padrão): jose acha JOSE, Jose, jose
- **Marcado:** busca exata

### Ajustar tamanho da fonte automaticamente

- **Marcado** (recomendado): mantém o tamanho original

### Tamanho da fonte manual

Slider de 6 a 24 — só ativa se desmarcar o auto-ajuste.

### Expandir caixa de texto

- **Marcado** (recomendado): permite substituições maiores
- **Desmarcado:** mantém a largura original

---

## 8. Exemplos práticos

### Exemplo 1 — Anonimizar um contrato

| Localizar | Substituir por |
|---|---|
| 111.111.111-11 | 000.000.000-00 |
| JOSE MARIA SILVA | CARLOS PATRICK SOUZA |
| jose.silva@email.com | anonimo@email.com |

**Modo:** Substituir texto. **Regex:** desmarcado.

### Exemplo 2 — Tarjar TODOS os CPFs de um lote

| Localizar | Substituir por |
|---|---|
| `\d{3}\.\d{3}\.\d{3}-\d{2}` | (deixe em branco) |

**Modo:** Tarjar. **Regex:** marcado.

### Exemplo 3 — Fluxo com scanner (recomendado)

1. Carregue o PDF
2. Clique em **Escanear PDF em busca de dados sensíveis**
3. Clique em **Marcar todos**
4. Clique em **Adicionar selecionados como regras**
5. Confirme que **Regex está DESATIVADO** no menu lateral
6. Clique em **Anonimizar PDF**
7. Baixe o resultado

---

## 9. Perguntas frequentes

**O texto antigo é realmente apagado?**
Sim. O app usa `apply_redactions()` do PyMuPDF, que remove o texto do fluxo de conteúdo do PDF.

**Meus arquivos ficam salvos em algum servidor?**
Não. Todo processamento ocorre em memória. Nada é armazenado.

**Funciona em PDF digitalizado (só imagem)?**
Não diretamente. Precisa de OCR antes.

**Quantas páginas suporta?**
Testado com 100+ páginas sem problema.

**O app guarda histórico das buscas?**
Não. Ao recarregar, tudo é zerado.

**Preciso criar conta?**
Não. Sem login, sem cadastro.

**Por que o scanner não achou nomes de pessoas?**
Nomes não têm formato fixo — não dá para pegar por Regex sem muitos falsos positivos. Adicione manualmente.

---

## 10. Solução de problemas

| Problema | Solução |
|---|---|
| Não encontrou a palavra | Use Regex com case-insensitive |
| Texto saiu cortado | Marque "Expandir caixa de texto" |
| Fonte grande/pequena demais | Desmarque auto, use slider |
| Erro ModuleNotFoundError: fitz | Confirme que requirements.txt existe e reinicie |
| App "dormiu" | Reabra a URL, acorda em ~30s |
| Lento em PDF gigante | Divida o PDF e processe em partes |
| Scanner não achou nada | O PDF pode ser imagem. Precisa OCR |
| Scanner achou coisa demais | Desmarque manualmente os falsos positivos |

---

## 11. Boas práticas

1. **Sempre teste em um PDF pequeno** (2-3 páginas) antes de um lote grande
2. **Guarde o PDF original** — sempre tenha backup
3. **Confira o resultado** abrindo o PDF e usando Ctrl+F para buscar o dado sensível
4. **Para dados realmente sensíveis**, use o modo **Tarjar**
5. **Use o Scanner** primeiro, depois complemente com regras manuais para nomes
6. **Use Regex** quando os dados têm padrão fixo

---

## Fluxo resumido (cola rápida)

1. Carregar PDF
2. (Opcional) Escanear dados sensíveis
3. (Opcional) Marcar e "Adicionar selecionados como regras"
4. Adicionar regras manuais se precisar
5. Escolher modo (Substituir / Tarjar)
6. (Opcional) Ativar Regex
7. Clicar em Anonimizar PDF
8. Clicar em Baixar PDF anonimizado