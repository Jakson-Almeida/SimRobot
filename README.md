# SimRobot - Simulador de Robô para Almoxarifado

Simulador de robô autônomo desenvolvido em Python usando Pygame para transporte de itens em um almoxarifado, com gerenciamento de bateria e cálculo de rotas otimizadas.

## 📋 Descrição do Projeto

O projeto consiste em um simulador onde um robô deve:
- **Transportar itens** de pontos de coleta para o almoxarifado
- **Respeitar a capacidade máxima** de itens que pode carregar (3 itens)
- **Gerenciar a bateria** e recarregar automaticamente quando necessário
- **Entregar itens automaticamente** no almoxarifado após 3 segundos parado
- **Calcular o melhor caminho** para otimizar o transporte (a implementar)

### Sistema de Itens:
- **2 tipos de itens** (TYPE_A e TYPE_B) com cores diferentes
- **Máximo de 2 itens por célula** tipo '1' (caminho livre)
- **Distribuição aleatória** de itens no início do jogo
- **Coleta manual** usando teclas 1 e 2
- **Entrega automática** no almoxarifado (1 item por segundo)

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

## 🚀 Funcionalidades Implementadas

### ✅ Sistema de Movimento e Bateria:
- [x] Interface visual com Pygame
- [x] Sistema de grid e visualização do ambiente
- [x] Movimento básico do robô (setas do teclado)
- [x] Sistema de bateria (diminui 2% por movimento)
- [x] Animação suave do robô
- [x] Visualização do nível de bateria
- [x] Validação de movimentos (não atravessa obstáculos)

### ✅ Sistema de Recarga Automática:
- [x] Recarga automática em estações 'R'
- [x] Espera de 3 segundos antes de iniciar recarga
- [x] Recarga linear (60 segundos para 0% a 100%)
- [x] Recarga proporcional ao nível atual (ex: 50% leva 30s)
- [x] Interrupção ao se mover
- [x] Mantém bateria em 100% quando já carregado na estação
- [x] Feedback visual com tempo restante

### ✅ Sistema de Itens:
- [x] Dois tipos de itens (TYPE_A e TYPE_B)
- [x] Máximo de 2 itens por célula tipo '1'
- [x] Capacidade do robô: 3 itens
- [x] Inicialização aleatória de itens nas células
- [x] Coleta de itens com teclas 1 e 2
- [x] Visualização de itens no grid (círculos coloridos)
- [x] Contador de itens carregados (canto superior direito do robô)

### ✅ Sistema de Entrega Automática:
- [x] Entrega automática no almoxarifado (célula 'A')
- [x] Espera de 3 segundos antes de iniciar entrega
- [x] Entrega de 1 item por segundo
- [x] Interrupção ao se mover
- [x] Feedback visual com status de entrega
- [x] Contador de itens entregues

### ❌ A Implementar:
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
- **Tecla '1'**: Coletar o primeiro item da célula atual
- **Tecla '2'**: Coletar o segundo item da célula atual
- **ESC/Fechar janela**: Sair

### Funcionalidades Automáticas:
- **Recarga**: Quando o robô fica parado por 3 segundos em uma estação de recarga ('R'), a recarga inicia automaticamente
- **Entrega**: Quando o robô fica parado por 3 segundos em um almoxarifado ('A') com itens, a entrega inicia automaticamente (1 item por segundo)

## 📝 Checklist de Implementação

### Fase 1: Estrutura de Dados
- [x] Definir quantidade total de itens a transportar
- [x] Definir capacidade máxima do robô (3 itens por viagem)
- [x] Criar lista/estrutura para pontos de coleta de itens
- [x] Adicionar variável para itens carregados no robô
- [x] Adicionar contador de itens entregues no almoxarifado

### Fase 2: Sistema de Coleta e Entrega
- [x] Implementar função para coletar itens (teclas 1 e 2)
- [x] Implementar função para entregar itens automaticamente (quando robô está em 'A')
- [x] Validar capacidade antes de coletar
- [x] Atualizar contadores (itens carregados, entregues, restantes)
- [x] Sistema de entrega automática com espera de 3 segundos
- [x] Entrega de 1 item por segundo

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
- [x] Mostrar itens carregados na tela (contador no robô)
- [x] Mostrar itens entregues/restantes
- [x] Indicar visualmente pontos de coleta (círculos coloridos)
- [x] Status de recarga com tempo restante
- [x] Status de entrega com itens restantes
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
├── Configurações (cores, tamanhos, matriz, itens)
├── Inicialização (pygame, posições, bateria, itens)
├── Funções de Desenho
│   ├── draw_grid()
│   ├── draw_items_on_grid()
│   ├── draw_robot()
│   ├── draw_robot_item_count()
│   ├── draw_battery()
│   └── draw_delivery_status()
├── Funções de Movimento
│   ├── move_robot()
│   └── animate_robot()
├── Funções de Recarga
│   ├── is_at_recharge_station()
│   └── update_auto_recharge()
├── Funções de Itens
│   ├── initialize_items_randomly()
│   ├── collect_item()
│   ├── is_at_warehouse()
│   └── update_auto_delivery()
└── Loop Principal
    └── Eventos e atualização da tela
```

## 📊 Parâmetros Configuráveis

### Sistema de Movimento:
- `CELL_SIZE`: Tamanho de cada célula (100px)
- `ANIMATION_SPEED`: Velocidade de animação (5)
- `battery`: Bateria inicial (100%)
- Consumo de bateria: 2% por movimento

### Sistema de Recarga:
- `RECHARGE_SPEED`: Tempo em segundos para recarregar de 0% a 100% (60s)
- `STATION_WAIT_TIME`: Tempo de espera antes de iniciar recarga (3000ms = 3s)

### Sistema de Itens:
- `MAX_ITEMS_PER_CELL`: Máximo de itens por célula tipo '1' (2)
- `ROBOT_CAPACITY`: Capacidade máxima do robô (3 itens)
- `ITEM_TYPES`: Tipos de itens disponíveis (TYPE_A, TYPE_B)

### Sistema de Entrega:
- `WAREHOUSE_WAIT_TIME`: Tempo de espera antes de iniciar entrega (3000ms = 3s)
- `DELIVERY_INTERVAL`: Intervalo entre entregas (1000ms = 1s por item)

## 🎮 Como Usar o Sistema

### Coleta de Itens:
1. Mova o robô até uma célula tipo '1' que contenha itens (círculos coloridos)
2. Pressione **1** para coletar o primeiro item ou **2** para coletar o segundo item
3. O contador de itens aparece no canto superior direito do robô quando há itens carregados

### Entrega de Itens:
1. Mova o robô até um almoxarifado (célula verde 'A')
2. Fique parado por 3 segundos
3. A entrega iniciará automaticamente (1 item por segundo)
4. O contador de itens entregues é exibido na tela

### Recarga de Bateria:
1. Mova o robô até uma estação de recarga (célula azul 'R')
2. Fique parado por 3 segundos
3. A recarga iniciará automaticamente
4. O tempo de recarga é proporcional ao nível atual (ex: 50% leva 30s)

## 🔧 Próximos Passos

1. Implementar algoritmo de busca de caminho (A* ou Dijkstra)
2. Adicionar lógica de planejamento automático
3. Implementar automação completa (sem controle manual)
4. Otimizar rotas considerando bateria e capacidade
5. Testar e otimizar

## 📄 Licença

Este é um projeto acadêmico desenvolvido como trabalho de curso.
