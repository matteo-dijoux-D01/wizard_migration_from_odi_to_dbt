## Conventions de l'entreprise

- Dans les couches bronze et silver, tout nom de colonne qui commence par une voyelle
  (a, e, i, o, u, y) est écrit en MAJUSCULES (exemples : EMAIL, ORDER_ID, ORDER_STATUS) ;
  les autres colonnes restent en minuscules (exemples : customer_id, product_id).
- La couche gold conserve les noms de colonnes des tables cibles ODI, afin de permettre
  le recettage colonne par colonne.
- Les descriptions YAML mentionnent cette convention quand elle s'applique.