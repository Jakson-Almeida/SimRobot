# SimRobot - Simulador de Robô para Almoxarifado

Simulador de robô autônomo desenvolvido em Python usando Pygame para transporte de itens em um almoxarifado, com gerenciamento de bateria e cálculo de rotas otimizadas.

## 📋 Descrição do Projeto

O projeto consiste em um simulador onde um robô deve:
- **Transportar itens** de pontos de coleta para o almoxarifado
- **Respeitar a capacidade máxima** de itens que pode carregar
- **Calcular o melhor caminho** para otimizar o transporte
- **Gerenciar a bateria** e recarregar quando necessário

## 🎯 Requisitos do Trabalho

Baseado nos requisitos fornecidos:
1. Há uma quantidade de itens a serem colocados no almoxarifado
2. O robô tem uma capacidade limitada de itens que consegue carregar
3. O robô deve mover esses itens e calcular o melhor caminho
4. O robô deve carregar suas baterias quando necessário

## 🗺️ Representação do Ambiente

O ambiente é representado por uma matriz onde cada célula pode ser:

| Símbolo | Significado | Cor |
|---------|-------------|-----|
| `'S'` | Posição inicial do robô (Start) | Amarelo |
| `'R'` | Estação de recarga (Recharge) | Azul |
| `'A'` | Almoxarifado (Armazém) | Verde |
| `'1'` | Caminho livre | Branco |
| `'0'` | Obstáculo | Cinza |

### Exemplo de Matriz:
```python
matriz2 = [
    ['A', '1', '1', 'R', 'A', '1'],
    ['1', '1', '1', '1', '1', '1'],
    ['1', '1', '1', '0', '1', '1'],
    ['1', 'S', '1', '1', '1', '1'],
]
```

## 🚀 Funcionalidades Atuais (Código Base)

### ✅ Implementado:
- [x] Interface visual com Pygame
- [x] Sistema de grid e visualização do ambiente
- [x] Movimento básico do robô (setas do teclado)
- [x] Sistema de bateria (diminui 2% por movimento)
- [x] Recarga em estações 'R' (tecla 'R')
- [x] Animação suave do robô
- [x] Visualização do nível de bateria
- [x] Validação de movimentos (não atravessa obstáculos)

### ❌ A Implementar:
- [ ] Sistema de itens (coleta e entrega)
- [ ] Capacidade máxima do robô
- [ ] Algoritmo de planejamento de caminho (A* ou Dijkstra)
- [ ] Automação completa (sem controle manual)
- [ ] Otimização de rotas considerando bateria e capacidade
- [ ] Múltiplas viagens quando necessário

## 📦 Dependências

```bash
pip install pygame
```

## 🎮 Como Executar (Versão Atual)

```bash
python Simrobot.py
```

### Controles:
- **Setas do teclado**: Mover o robô (↑ ↓ ← →)
- **Tecla 'R'**: Recarregar bateria (quando estiver em uma estação 'R')
- **ESC/Fechar janela**: Sair

## 📝 Checklist de Implementação

### Fase 1: Estrutura de Dados
- [ ] Definir quantidade total de itens a transportar
- [ ] Definir capacidade máxima do robô (quantos itens por viagem)
- [ ] Criar lista/estrutura para pontos de coleta de itens
- [ ] Adicionar variável para itens carregados no robô
- [ ] Adicionar contador de itens entregues no almoxarifado

### Fase 2: Sistema de Coleta e Entrega
- [ ] Implementar função para coletar itens (quando robô está em ponto de coleta)
- [ ] Implementar função para entregar itens (quando robô está em 'A')
- [ ] Validar capacidade antes de coletar
- [ ] Atualizar contadores (itens carregados, entregues, restantes)

### Fase 3: Algoritmo de Caminho
- [ ] Implementar busca de caminho (A* ou Dijkstra)
- [ ] Considerar obstáculos ('0') no cálculo
- [ ] Calcular distância entre pontos
- [ ] Função para encontrar melhor caminho entre dois pontos

### Fase 4: Planejamento Inteligente
- [ ] Decidir quando recarregar (ex: bateria < 30%)
- [ ] Planejar rota: coleta → almoxarifado → recarga (se necessário)
- [ ] Otimizar múltiplas viagens
- [ ] Calcular se há bateria suficiente para completar viagem

### Fase 5: Automação
- [ ] Remover controle manual (setas do teclado)
- [ ] Implementar loop automático de execução
- [ ] Executar sequência: planejar → mover → coletar → entregar → recarregar
- [ ] Parar quando todos os itens forem entregues

### Fase 6: Visualização e Feedback
- [ ] Mostrar itens carregados na tela
- [ ] Mostrar itens entregues/restantes
- [ ] Indicar visualmente pontos de coleta
- [ ] Mostrar caminho planejado (opcional)
- [ ] Mensagem de conclusão quando terminar

### Fase 7: Testes e Ajustes
- [ ] Testar com diferentes quantidades de itens
- [ ] Testar com diferentes capacidades do robô
- [ ] Testar cenários de bateria baixa
- [ ] Validar que todos os itens são entregues
- [ ] Ajustar parâmetros (consumo de bateria, velocidade, etc.)

## 💡 Sugestões de Implementação

### 1. Pontos de Coleta
- Adicionar novo símbolo na matriz (ex: `'I'` para Item)
- Ou definir coordenadas específicas como pontos de coleta

### 2. Algoritmo de Caminho
- **A*** é recomendado para este caso
- Considerar custo baseado em distância e bateria disponível

### 3. Estratégia de Recarga
- Recarregar quando bateria < 30%
- Ou quando não há bateria suficiente para completar a viagem

### 4. Múltiplas Viagens
- Calcular quantas viagens são necessárias: `ceil(itens_totais / capacidade)`
- Planejar cada viagem considerando bateria e distância

## 🏗️ Estrutura do Código

```
Simrobot.py
├── Configurações (cores, tamanhos, matriz)
├── Inicialização (pygame, posições, bateria)
├── Funções de Desenho
│   ├── draw_grid()
│   ├── draw_robot()
│   └── draw_battery()
├── Funções de Movimento
│   ├── move_robot()
│   ├── animate_robot()
│   └── recharge()
└── Loop Principal
    └── Eventos e atualização da tela
```

## 📊 Parâmetros Configuráveis

- `CELL_SIZE`: Tamanho de cada célula (100px)
- `ANIMATION_SPEED`: Velocidade de animação (5)
- `battery`: Bateria inicial (100%)
- Consumo de bateria: 2% por movimento

## 🔧 Próximos Passos

1. Definir estrutura de dados para itens
2. Implementar algoritmo de busca de caminho
3. Criar sistema de coleta e entrega
4. Adicionar lógica de planejamento automático
5. Testar e otimizar

## 📄 Licença

Este é um projeto acadêmico desenvolvido como trabalho de curso.
