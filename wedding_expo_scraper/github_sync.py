#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub 동기화 모듈 - 자동 커밋 및 푸시
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from git import Repo
from git.exc import GitCommandError

from .config import PROJECT_ROOT, GITHUB_TOKEN, GITHUB_REPO_URL, CSV_PATH


logger = logging.getLogger(__name__)


class GitHubSync:
    """GitHub 동기화 클래스"""
    
    def __init__(self, repo_path: Optional[Path] = None):
        self.repo_path = repo_path or PROJECT_ROOT
        self.repo: Optional[Repo] = None
        
    def _get_repo(self) -> Repo:
        """저장소 객체 가져오기 (캐싱)"""
        if self.repo is None:
            self.repo = Repo(self.repo_path)
        return self.repo
    
    def is_git_repo(self) -> bool:
        """Git 저장소인지 확인"""
        try:
            Repo(self.repo_path)
            return True
        except Exception:
            return False
    
    def init_repo(self) -> bool:
        """Git 저장소 초기화"""
        try:
            if self.is_git_repo():
                logger.info("이미 Git 저장소입니다.")
                return True
            
            repo = Repo.init(self.repo_path)
            logger.info(f"✅ Git 저장소 초기화: {self.repo_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Git 초기화 실패: {e}")
            return False
    
    def configure_remote(self, remote_url: Optional[str] = None) -> bool:
        """원격 저장소 설정"""
        url = remote_url or GITHUB_REPO_URL
        
        if not url:
            logger.warning("GitHub URL이 설정되지 않았습니다.")
            return False
        
        try:
            repo = self._get_repo()
            
            # 기존 origin 확인
            if 'origin' in repo.remotes:
                repo.remotes.origin.set_url(url)
                logger.info(f"✅ 원격 URL 업데이트: {url}")
            else:
                repo.create_remote('origin', url)
                logger.info(f"✅ 원격 추가: {url}")
            
            return True
            
        except GitCommandError as e:
            logger.error(f"❌ 원격 설정 실패: {e}")
            return False
    
    def configure_https_auth(self) -> bool:
        """HTTPS 인증 설정 (Token)"""
        token = GITHUB_TOKEN
        
        if not token:
            logger.warning("GitHub Token이 설정되지 않았습니다.")
            return False
        
        try:
            repo = self._get_repo()
            
            # 현재 URL 가져오기
            if 'origin' not in repo.remotes:
                logger.error("원격 저장소가 설정되지 않았습니다.")
                return False
            
            remote = repo.remotes.origin
            current_url = remote.url
            
            # 토큰 기반 URL로 변환
            if 'github.com' in current_url:
                # URL에서 사용자명 추출
                parts = current_url.replace('https://github.com/', '').replace('.git', '').split('/')
                if len(parts) >= 2:
                    username = parts[0]
                    new_url = f"https://{token}@github.com/{username}/{parts[1]}.git"
                    remote.set_url(new_url)
                    logger.info("✅ GitHub Token 인증 설정 완료")
                    return True
            
            logger.warning("URL 형식이 올바르지 않습니다.")
            return False
            
        except GitCommandError as e:
            logger.error(f"❌ 인증 설정 실패: {e}")
            return False
    
    def has_changes(self) -> bool:
        """변경 사항 확인"""
        try:
            repo = self._get_repo()
            return repo.is_dirty(untracked_files=True)
        except Exception:
            return False
    
    def get_changes_summary(self) -> str:
        """변경 사항 요약"""
        try:
            repo = self._get_repo()
            
            modified = [item.a_path for item in repo.index.diff('HEAD')]
            untracked = repo.untracked_files
            
            summary = []
            if modified:
                summary.append(f"수정: {len(modified)}개 파일")
                for f in modified[:5]:
                    summary.append(f"  - {f}")
            if untracked:
                summary.append(f"신규: {len(untracked)}개 파일")
                for f in untracked[:5]:
                    summary.append(f"  - {f}")
            
            return '\n'.join(summary) if summary else "변경 사항 없음"
            
        except Exception as e:
            logger.error(f"변경 요약 실패: {e}")
            return "알 수 없음"
    
    def add_all(self) -> bool:
        """모든 변경 사항 스테이징"""
        try:
            repo = self._get_repo()
            repo.git.add(A=True)
            logger.info("✅ 모든 파일 스테이징 완료")
            return True
        except GitCommandError as e:
            logger.error(f"❌ 스테이징 실패: {e}")
            return False
    
    def commit(self, message: Optional[str] = None) -> bool:
        """변경 사항 커밋"""
        try:
            repo = self._get_repo()
            
            # 커밋 메시지 생성
            if not message:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                message = f"📅 웨딩박람회 데이터 업데이트 - {timestamp}\n\n{self.get_changes_summary()}"
            
            # 커밋 실행
            repo.index.commit(message)
            logger.info(f"✅ 커밋 완료: {message[:50]}...")
            return True
            
        except GitCommandError as e:
            if 'nothing to commit' in str(e).lower():
                logger.info("변경 사항이 없어 커밋을 건너뜁니다.")
            else:
                logger.error(f"❌ 커밋 실패: {e}")
            return False
    
    def pull(self) -> bool:
        """원격에서 풀"""
        try:
            repo = self._get_repo()
            
            if 'origin' not in repo.remotes:
                logger.info("원격 저장소가 없어 풀을 건너뜁니다.")
                return True
            
            origin = repo.remotes.origin
            origin.pull()
            logger.info("✅ 풀 완료")
            return True
            
        except GitCommandError as e:
            logger.warning(f"⚠️ 풀 실패 (계속 진행): {e}")
            return False
    
    def push(self) -> bool:
        """원격에 푸시"""
        try:
            repo = self._get_repo()
            
            if 'origin' not in repo.remotes:
                logger.error("원격 저장소가 설정되지 않았습니다.")
                return False
            
            origin = repo.remotes.origin
            origin.push(refspec=f"HEAD:refs/heads/{repo.active_branch.name}")
            logger.info("✅ 푸시 완료")
            return True
            
        except GitCommandError as e:
            logger.error(f"❌ 푸시 실패: {e}")
            return False
    
    def sync(self, auto_commit: bool = True, auto_push: bool = True) -> bool:
        """전체 동기화流程"""
        try:
            # Git 저장소 확인
            if not self.is_git_repo():
                logger.error("Git 저장소가 아닙니다. 먼저 git init을 실행하세요.")
                return False
            
            # 변경 사항 확인
            if not self.has_changes():
                logger.info("변경 사항이 없어 동기화를 건너뜁니다.")
                return True
            
            # 풀 (Konflik 방지)
            self.pull()
            
            # 커밋
            if auto_commit:
                if not self.commit():
                    return False
            
            # 푸시
            if auto_push:
                if not self.push():
                    return False
            
            logger.info("✅ GitHub 동기화 완료")
            return True
            
        except Exception as e:
            logger.error(f"❌ 동기화 실패: {e}", exc_info=True)
            return False
    
    def setup(self, remote_url: Optional[str] = None) -> bool:
        """저장소 초기 설정 (첫 실행 시)"""
        logger.info("=" * 50)
        logger.info("🔧 GitHub 저장소 설정 시작")
        logger.info("=" * 50)
        
        # 1. Git 초기화
        if not self.init_repo():
            return False
        
        # 2. 원격 저장소 설정
        if remote_url or GITHUB_REPO_URL:
            if not self.configure_remote(remote_url):
                return False
        
        # 3. HTTPS 인증 설정
        if GITHUB_TOKEN:
            self.configure_https_auth()
        
        # 4. 초기 커밋
        self.add_all()
        if self.has_changes():
            self.commit("Initial commit: Wedding Expo Scraper")
            
            # 첫 푸시
            if 'origin' in self._get_repo().remotes:
                try:
                    self.push()
                except Exception as e:
                    logger.warning(f"첫 푸시 실패: {e}")
                    logger.info("원격 저장소가 존재하지 않으면 먼저 GitHub에서 저장소를 생성하세요.")
        
        logger.info("✅ GitHub 설정 완료")
        return True


if __name__ == "__main__":
    # 테스트
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s - %(message)s'
    )
    
    sync = GitHubSync()
    
    # 저장소 상태 확인
    if sync.is_git_repo():
        print("✅ Git 저장소")
        if sync.has_changes():
            print("📝 변경 사항 있음")
            print(sync.get_changes_summary())
        else:
            print("✅ 변경 사항 없음")
    else:
        print("⚠️ Git 저장소가 아닙니다")
