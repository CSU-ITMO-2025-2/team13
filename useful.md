```
helm install team13-app ./k8s/helm/team13-app -n team13-ns -f ./k8s/helm/team13-app/values.yaml -f secrets.yaml --kubeconfig team13-kubeconfig.yaml
```

```
kubectl get pods -n team13-ns --kubeconfig team13-kubeconfig.yaml
```

```
kubectl get all -n team13-ns --kubeconfig team13-kubeconfig.yaml
```

```
kubectl describe rs auth-service -n team13-ns --kubeconfig team13-kubeconfig.yaml
```

```
helm upgrade team13-app ./k8s/helm/team13-app -n team13-ns -f ./k8s/helm/team13-app/values.yaml -f secrets.yaml --kubeconfig team13-kubeconfig.yaml
```

```
kubectl get ingress -n team13-ns --kubeconfig team13-kubeconfig.yaml
```

```
docker build -t ddreamboyy/team13-bff:v2 .
docker push ddreamboyy/team13-bff:v2
kubectl delete pod -l app=bff-service -n team13-ns --kubeconfig team13-kubeconfig.yaml
kubectl get pods -n team13-ns --kubeconfig team13-kubeconfig.yaml
```

```
kubectl top pods -n team13-ns --kubeconfig team13-kubeconfig.yaml
```

```
kubectl logs -l app=bff-service -n team13-ns --kubeconfig team13-kubeconfig.yaml
```

```
kubectl exec -it ... -n team13-ns --kubeconfig team13-kubeconfig.yaml -- /bin/sh
```


```
kubectl port-forward svc/kafka-ui 8080:80 -n kafka
```

```
kubectl apply -f k8s-secrets.yaml -n team13-ns --kubeconfig team13-kubeconfig.yaml
```

```
kubectl get secret team13-secrets -n team13-ns --kubeconfig team13-kubeconfig.yaml
```

```
kubectl port-forward svc/rabbitmq 15672:15672 -n team13-ns --kubeconfig team13-kubeconfig.yaml
```