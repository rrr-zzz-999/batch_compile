#!/usr/bin/env python3
"""
简单的编译检查脚本 - 告诉你哪些合约可以编译，哪些不能
"""
import json
import os
import subprocess
import sys

def test_compile(contract_path, solc_binary):
    """测试编译单个合约"""
    try:
        cmd = [solc_binary, "--bin", contract_path]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stderr if result.returncode != 0 else ""
    except Exception as e:
        return False, str(e)

def main():
    # 读取合约列表
    with open('main.json', 'r', encoding='utf-8') as f:
        contracts = json.load(f)
    
    # 自动发现所有可用的编译器
    import glob
    compiler_files = glob.glob("./solc-*") + ["./solc"]
    available_compilers = [c for c in compiler_files if os.path.exists(c) and os.access(c, os.X_OK)]
    
    # 按版本排序（新版本优先）
    available_compilers.sort(key=lambda x: x.replace("./solc-", "").replace("./solc", "0.8.19"), reverse=True)
    
    if not available_compilers:
        print("❌ 没有找到可用的solc编译器")
        return
    
    print(f"使用编译器: {', '.join(available_compilers)}")
    print(f"检查 {len(contracts)} 个合约...")
    print("=" * 50)
    
    can_compile = []
    cannot_compile = []
    
    for project_name, contract_path in contracts.items():
        print(f"检查 {project_name}...", end=" ")
        
        # 检查文件是否存在
        if not os.path.exists(contract_path):
            print("❌ 文件不存在")
            cannot_compile.append((project_name, "文件不存在"))
            continue
        
        # 尝试所有编译器
        compiled = False
        error_msg = ""
        for compiler in available_compilers:
            success, error = test_compile(contract_path, compiler)
            if success:
                compiled = True
                break
            else:
                if not error_msg:  # 保存第一个错误信息
                    error_msg = error[:200] if error else "编译失败"
        
        if compiled:
            print("✅ 可以编译")
            can_compile.append(project_name)
        else:
            print("❌ 无法编译")
            cannot_compile.append((project_name, error_msg))
    
    # 输出结果
    print("\n" + "=" * 50)
    print("📊 编译检查结果:")
    print(f"总计: {len(contracts)} 个合约")
    print(f"✅ 可以编译: {len(can_compile)} 个")
    print(f"❌ 无法编译: {len(cannot_compile)} 个")
    
    if can_compile:
        print(f"\n✅ 可以编译的合约 ({len(can_compile)}个):")
        for i, project in enumerate(can_compile, 1):
            print(f"  {i:2d}. {project}")
    
    if cannot_compile:
        print(f"\n❌ 无法编译的合约 ({len(cannot_compile)}个):")
        for i, (project, reason) in enumerate(cannot_compile, 1):
            print(f"  {i:2d}. {project} ({reason})")
    
    # 保存简单结果
    result = {
        "can_compile": can_compile,
        "cannot_compile": [{"project": p, "reason": r} for p, r in cannot_compile],
        "summary": {
            "total": len(contracts),
            "success": len(can_compile),
            "failed": len(cannot_compile)
        }
    }
    
    with open('compile_check_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 详细结果已保存到 compile_check_result.json")

if __name__ == "__main__":
    main()
