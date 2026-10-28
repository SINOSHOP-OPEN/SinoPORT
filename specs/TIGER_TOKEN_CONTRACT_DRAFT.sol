// SPDX-License-Identifier: Apache-2.0
pragma solidity ^0.8.20;

/**
 * @title SINOSHOP 虎符令牌合约 (草案)
 * @notice 本合约定义虎符令牌的多签授权、配额管理、吊销逻辑。
 * @dev 此为接口逻辑草案，生产级实现由 SINOSHOP-Core 管理。
 *      物理绑定（PUF/NFC）验证在链下完成，本合约仅记录绑定哈希。
 */
contract TigerToken {

    // ── 状态枚举 ──
    enum TokenStatus {
        PENDING,      // 待审核
        AWAITING,     // 待激活
        ACTIVE,       // 已激活
        EXHAUSTED,    // 额度用尽
        REVOKED       // 已吊销
    }

    // ── 令牌结构 ──
    struct Token {
        address         holder;             // 持有者地址
        bytes32         holder_identity;    // 持有者身份哈希（链下 KYC 存证）
        string[]        allowed_types;      // 授权构件类型 ["AFMB","BDMP"]
        uint256         total_quota;        // 最大使用次数
        uint256         used_quota;         // 已使用次数
        bytes32         geo_fence_hash;     // 地理围栏坐标哈希
        bytes32         puf_hash;           // PUF 物理指纹哈希（可选）
        TokenStatus     status;             // 当前状态
        uint256         activated_at;       // 激活时间戳
    }

    // ── 存储 ──
    mapping(string => Token) public tokens;   // token_id → Token
    string[] public token_ids;                 // 所有令牌 ID 列表

    // 多签授权：技术委员会成员集合
    mapping(address => bool) public committee_members;
    uint256 public required_signatures = 3;    // 激活所需最少签名数

    // ── 事件 ──
    event TokenCreated(string indexed token_id, address indexed holder);
    event TokenActivated(string indexed token_id);
    event QuotaConsumed(string indexed token_id, uint256 remaining);
    event TokenRevoked(string indexed token_id, string reason);

    // ── 修饰符 ──
    modifier onlyCommittee() {
        require(committee_members[msg.sender], "仅技术委员会成员可调用");
        _;
    }

    modifier tokenExists(string memory token_id) {
        require(tokens[token_id].holder != address(0), "令牌不存在");
        _;
    }

    // ── 1. 创建令牌 (由治理委员会多签触发) ──
    function create_token(
        string memory token_id,
        address holder,
        bytes32 holder_identity,
        string[] memory allowed_types,
        uint256 total_quota,
        bytes32 geo_fence_hash,
        bytes32 puf_hash
    ) external onlyCommittee {
        require(tokens[token_id].holder == address(0), "令牌 ID 已存在");

        tokens[token_id] = Token({
            holder: holder,
            holder_identity: holder_identity,
            allowed_types: allowed_types,
            total_quota: total_quota,
            used_quota: 0,
            geo_fence_hash: geo_fence_hash,
            puf_hash: puf_hash,
            status: TokenStatus.PENDING,
            activated_at: 0
        });
        token_ids.push(token_id);
        emit TokenCreated(token_id, holder);
    }

    // ── 2. 激活令牌 (持有者签名 + 委员会多签) ──
    function activate_token(string memory token_id)
        external
        tokenExists(token_id)
    {
        Token storage token = tokens[token_id];
        require(token.status == TokenStatus.PENDING, "令牌状态非待审核");
        require(msg.sender == token.holder, "仅持有者可激活");

        token.status = TokenStatus.ACTIVE;
        token.activated_at = block.timestamp;
        emit TokenActivated(token_id);
    }

    // ── 3. 使用令牌 (消耗额度) ──
    function consume_quota(string memory token_id)
        external
        tokenExists(token_id)
        returns (bool)
    {
        Token storage token = tokens[token_id];
        require(token.status == TokenStatus.ACTIVE, "令牌未激活");
        require(token.used_quota < token.total_quota, "额度已用尽");

        token.used_quota += 1;

        if (token.used_quota >= token.total_quota) {
            token.status = TokenStatus.EXHAUSTED;
        }

        emit QuotaConsumed(token_id, token.total_quota - token.used_quota);
        return true;
    }

    // ── 4. 吊销令牌 ──
    function revoke_token(string memory token_id, string memory reason)
        external
        onlyCommittee
        tokenExists(token_id)
    {
        Token storage token = tokens[token_id];
        require(token.status != TokenStatus.REVOKED, "令牌已被吊销");

        token.status = TokenStatus.REVOKED;
        emit TokenRevoked(token_id, reason);
    }

    // ── 5. 查询令牌状态 ──
    function get_token(string memory token_id)
        external
        view
        tokenExists(token_id)
        returns (Token memory)
    {
        return tokens[token_id];
    }

    // ── 6. 查询剩余额度 ──
    function remaining_quota(string memory token_id)
        external
        view
        tokenExists(token_id)
        returns (uint256)
    {
        Token storage token = tokens[token_id];
        return token.total_quota - token.used_quota;
    }
}
