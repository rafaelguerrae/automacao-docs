"""
Processador de dados JSON para conversão em estruturas IDML.
"""
import json
from typing import Dict, List, Any
import uuid


class JSONProcessor:
    """Processa dados JSON e os converte para estruturas compatíveis com IDML."""
    
    def __init__(self):
        self.secoes_processadas = []
        
    def processar_json(self, dados_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Processa o JSON de entrada e retorna uma lista de seções estruturadas.
        
        Args:
            dados_json: Dicionário com os dados JSON de entrada
            
        Returns:
            Lista de seções processadas com metadados para IDML
        """
        if 'secoes' not in dados_json:
            raise ValueError("JSON deve conter uma chave 'secoes'")
            
        secoes = dados_json['secoes']
        self.secoes_processadas = []
        
        for i, secao in enumerate(secoes):
            secao_processada = self._processar_secao(secao, i)
            self.secoes_processadas.append(secao_processada)
            
        return self.secoes_processadas
    
    def _processar_secao(self, secao: Dict[str, Any], indice: int) -> Dict[str, Any]:
        """
        Processa uma seção individual.
        
        Args:
            secao: Dados da seção
            indice: Índice da seção na lista
            
        Returns:
            Seção processada com metadados
        """
        # Gerar ID único se não existir
        secao_id = secao.get('id', f'secao_{indice}')
        
        # Gerar UUIDs para elementos IDML
        story_id = self._gerar_uuid()
        text_frame_id = self._gerar_uuid()
        
        return {
            'id': secao_id,
            'titulo': secao.get('titulo', ''),
            'texto': secao.get('texto', ''),
            'indice': indice,
            'story_id': story_id,
            'text_frame_id': text_frame_id,
            'posicao_y': 50 + (indice * 100)  # Posicionamento básico
        }
    
    def _gerar_uuid(self) -> str:
        """Gera UUID único para elementos IDML."""
        return f"u{uuid.uuid4().hex[:6]}"
    
    def obter_secoes_processadas(self) -> List[Dict[str, Any]]:
        """Retorna as seções processadas."""
        return self.secoes_processadas
    
    def validar_json(self, dados_json: Dict[str, Any]) -> bool:
        """
        Valida se o JSON está no formato esperado.
        
        Args:
            dados_json: Dados JSON para validar
            
        Returns:
            True se válido, False caso contrário
        """
        if not isinstance(dados_json, dict):
            return False
            
        if 'secoes' not in dados_json:
            return False
            
        secoes = dados_json['secoes']
        if not isinstance(secoes, list):
            return False
            
        for secao in secoes:
            if not isinstance(secao, dict):
                return False
            if 'titulo' not in secao or 'texto' not in secao:
                return False
                
        return True 