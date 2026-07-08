#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo "🔍 Проверка YAML-файлов и Ingress-ресурсов..."

# 1. Проверка синтаксиса всех YAML-файлов
echo ""
echo "📄 Проверка синтаксиса YAML-файлов..."

find . -name "*.yaml" -o -name "*.yml" | while read -r file; do
    if command -v yq &> /dev/null; then
        if yq eval 'true' "$file" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $file - синтаксис корректный${NC}"
        else
            echo -e "${RED}❌ $file - ОШИБКА СИНТАКСИСА${NC}"
            yq eval 'true' "$file" 2>&1 | head -5
        fi
    else
        echo -e "${YELLOW}⚠️  yq не установлен. Установи: brew install yq${NC}"
        break
    fi
done

# 2. Проверка наличия Ingress-ресурсов
echo ""
echo "🌐 Проверка Ingress-ресурсов..."

find . -type f \( -name "*.yaml" -o -name "*.yml" \) | while read -r file; do
    if grep -q "kind: Ingress" "$file"; then
        echo -e "${YELLOW}🔎 Найден Ingress в файле: $file${NC}"
        
        # Проверка обязательных полей
        if grep -q "host:" "$file" && grep -q "serviceName:" "$file" && grep -q "servicePort:" "$file"; then
            echo -e "${GREEN}   ✅ Ingress содержит все обязательные поля (host, serviceName, servicePort)${NC}"
        else
            echo -e "${RED}   ❌ Ingress НЕ содержит обязательные поля!${NC}"
            echo "   Проверь наличие полей: host, serviceName, servicePort"
        fi
    fi
done

# 3. Проверка Helm-чарта (если есть)
if [ -d "flask-chart" ]; then
    echo ""
    echo "📦 Проверка Helm-чарта..."
    
    # Проверка синтаксиса шаблонов
    if command -v helm &> /dev/null; then
        echo "🔧 Проверка Helm-шаблонов..."
        if helm template flask-chart > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Helm-шаблоны синтаксически корректны${NC}"
        else
            echo -e "${RED}❌ Ошибка в Helm-шаблонах:${NC}"
            helm template flask-chart 2>&1 | head -10
        fi
    else
        echo -e "${YELLOW}⚠️  Helm не установлен. Установи: brew install helm${NC}"
    fi
fi

# 4. Проверка Ingress-ресурсов в кластере (через kubectl)
echo ""
echo "☸️  Проверка Ingress-ресурсов в кластере..."

if command -v kubectl &> /dev/null; then
    echo "📋 Список Ingress-ресурсов:"
    kubectl get ingress -A 2>/dev/null || echo -e "${RED}❌ Не удалось получить список Ingress${NC}"
    
    echo ""
    echo "🔍 Детальная проверка Ingress-ресурсов через --dry-run:"
    kubectl get ingress -A -o yaml | grep -A 10 "kind: Ingress" | head -30 || echo "Ingress не найден"
else
    echo -e "${RED}❌ kubectl не установлен${NC}"
fi

echo ""
echo "✅ Проверка завершена."
