# pacman
Juego de pacman Simple sin colición ni sistema de puntuación

## Ghost RANDOM
Los fantasmas con movimiento aleatorio funcionan mediante update_dir_random() que obtiene las direcciones posibles desde el nodo actual, quita la dirección reversa y elige aleatoriamente entre estas, actualiza el atributo dir_id para cambiar la dirección del fantasma

## Ghost SEEK
Los fantasmas cazadores, mediante update2() llaman a las funciones update_dir_seeker() y update_dir_random() dependiendo del estado del contador mode_counter, el cual determina el valor de la variable de conrol 'mode'. Cuando el contador es positivo, el fantasma está en modo caza (CHASE), cuando es negativo está en modo aleatorio (RANDOM). Esto se hizo con el fin de emular el comportamiento de los fantasmas del juego oficial en el que persiguen al pacman por un determinado tiempo y posteriormente vuelven a comportarse como fantasmas aleatorios, de modo que dan tiempo al jugador de escapar y el juego no se hace en extremo complicado.

## Ghost SEEKCOOP
Los fantasmas cooperativos van en pares, mediante update3() los fantasmas de tipo cooperativo comparten sus variables. Uno de los fantasmas cooperativos debe designarse como "master" pasando el parametro True al ultimo argumento de update3(), esto es para que solo uno de los fantasmas controle las variables de control 'mode' y 'roll'. 'roll' define el comportamiento del fantasma cooperativo, cuando es LEADER se comporta como un fantasma cazador normal, es decir, llama a astar() que es el algoritmo A* sin modificaciones para determinar el mejor camino y su siguiente nodo; en cambio, cuando el valor es HELPER, el fantasma llama a la función update_dir_coop_seeker(), que entre otros parametros, recibe a su fantasma compañero (con roll = LEADER) por referencia, así puede acceder a su atributo 'path' que es el camino dado por astar() y evaluar astar_coop() que pondera cada hoja del arbol con una penalización si está cerca de la posición futura posible de su compañero LEADER, evitando así que se junten demasiado.

'roll' cambia a partir del fantasma 'master', el cual evalua en cada nodo la distnacia de ambos fantasmas al pacamn, quien esté más cerca se convierte en el nuevo LEADER
