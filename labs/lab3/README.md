## Важность порядка применения ресурсов

Порядок имеет значение, потому что `Deployment` использует `ConfigMap` и `Secret`.

Если применить `Deployment` раньше — pod не будет создан.

### Корректный порядок применения:
1. `ConfigMap` и `Secret`
2. `Service`
3. `Deployment`

---

## Локальный доступ к сервису

Для локального доступа к сервису используется `Service` типа `NodePort`.

Туннелирование трафика выполняется командой:## Важность порядка применения ресурсов

Порядок имеет значение, потому что `Deployment` использует `ConfigMap` и `Secret`.

Если применить `Deployment` раньше — pod не будет создан.

### Корректный порядок применения:
1. `ConfigMap` и `Secret`
2. `Service`
3. `Deployment`

---

## Локальный доступ к сервису

Для локального доступа к сервису используется `Service` типа `NodePort`.

Туннелирование трафика выполняется командой:
kubectl exec -it deployment/nextcloud -- curl http://localhost/status.php



![Состояние pod’ов в кластере (kubectl get pods)](images/kubectl-get-pods.png)
![Web-интерфейс Nextcloud](images/nextcloud-ui.png)
![Общее состояние кластера в Kubernetes Dashboard](images/dashboard-overview.png)
![Deployments, Pods и ReplicaSets в Kubernetes Dashboard](images/deployments-pods.png)
![Проверка health-endpoint Nextcloud (/status.php)](images/health_check.png)
