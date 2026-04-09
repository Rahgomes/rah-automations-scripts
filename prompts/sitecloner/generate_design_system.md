# Prompt: Geração de Design System a partir de HTML/CSS (SiteCloner)

## Objetivo
Analisar o código HTML e CSS fornecido de um website clonado para extrair e documentar seus componentes visuais e de interação, resultando em um Design System funcional e compreensível. O Design System deve ser apresentado de forma estruturada, facilitando a implementação em novos projetos (e.g., React, Next.js, Tailwind CSS).

## Contexto
O input será o código-fonte (HTML, CSS e JavaScript relevante) de uma página web. O foco é identificar padrões, elementos reutilizáveis e as diretrizes de estilo subjacentes.

## Instruções para a IA
Dado o código HTML, CSS e JavaScript de uma página web, execute as seguintes etapas:

1.  **Análise de Cores:**
    *   Liste a paleta de cores primárias, secundárias e neutras (com seus respectivos códigos HEX/RGB/HSL).
    *   Identifique o uso das cores em backgrounds, textos, botões e elementos de destaque.
    *   Categorize-as como cores de marca, de feedback (sucesso, erro, alerta), etc.

2.  **Análise de Tipografia:**
    *   Identifique as famílias de fontes utilizadas (primária, secundária, fallback).
    *   Liste os tamanhos de fonte (px, rem, em) para títulos (h1-h6), parágrafos, e outros elementos textuais.
    *   Determine os pesos de fonte (light, regular, bold) e estilos (itálico).
    *   Identifique o  e  padrão.

3.  **Componentes de UI:**
    *   Liste e descreva os principais componentes reutilizáveis encontrados (ex: Botões, Cards, Formulários (inputs, labels), Navegação (menus, links), Modais, Banners, Badges, etc.).
    *   Para cada componente, descreva sua estrutura HTML básica, as classes CSS associadas e as variações (ex: , , ).
    *   Identifique seus estados (hover, active, focus, disabled).

4.  **Espaçamento e Layout:**
    *   Identifique os padrões de espaçamento (margin, padding) utilizados (ex: small, medium, large, ou múltiplos de uma base).
    *   Descreva a estratégia de layout (Flexbox, Grid) e como os elementos são alinhados e distribuídos.
    *   Identifique breakpoints responsivos e como o layout se adapta.

5.  **Ícones e Imagens:**
    *   Identifique o uso de bibliotecas de ícones (se houver, ex: Font Awesome, Material Icons).
    *   Descreva padrões de uso de imagens (sizes, lazy loading, aspect ratios).

6.  **Saída Final:**
    *   Apresente o Design System de forma clara e hierárquica, utilizando Markdown.
    *   Inclua exemplos de snippets de HTML/CSS para os componentes se possível, ou uma descrição detalhada que permita recriá-los.

## Restrições
*   Foco em extração do design visual e interativo. Não refatorar o código, apenas documentá-lo.
*   Priorizar padrões e elementos reutilizáveis.

---
