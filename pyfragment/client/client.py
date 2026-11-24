from pyfragment.client.account import AccountMethods
from pyfragment.client.marketplace import MarketplaceMethods
from pyfragment.client.numbers import NumberMethods
from pyfragment.client.purchases import PurchaseMethods


class FragmentClient(PurchaseMethods, MarketplaceMethods, NumberMethods, AccountMethods):
    """
    Client for the Fragment.com API.

    .. note::
        This library is not affiliated with, endorsed by, or in any way officially
        connected with Fragment or Telegram.

    Args:
        seed: Mnemonic phrase of the GRAM (ex TON) wallet.
        api_key: API key for the chosen provider — tonconsole.com (default) or t.me/toncenter.
        cookies: Fragment session cookies as a dict or JSON string. ``stel_token`` and ``stel_ton_token`` are required;
            ``stel_ssid`` and ``stel_dt`` are optional.
        wallet_version: Wallet contract — ``"V5R1"`` (default), ``"V4R2"``, ``"HighloadV2"``,
            ``"HighloadV3R1"``, or ``"TG"`` for a Telegram Wallet (12 words, or 24 after a key rotation).
        mnemonic_type: How the phrase derives the key — ``"ton"`` (default: Tonkeeper, MyTonWallet and
            other TON wallets, 12 or 24 words) or ``"multichain"`` (a BIP-39 phrase of a multichain
            wallet, 12 to 24 words). A Telegram Wallet always uses ``"multichain"``.
        api_provider: Blockchain API provider — ``"tonapi"`` (tonconsole.com, default)
            or ``"toncenter"`` (t.me/toncenter).
        timeout: HTTP request timeout in seconds. Defaults to ``30.0``.
        headers: Custom HTTP request headers. If omitted, :data:`BASE_HEADERS` is used.
        confirm_timeout: Seconds to wait for Fragment to confirm a purchase after paying. ``0`` reports it
            right away (``confirmed=False``). Defaults to ``60``.
        on_transfer_prepared: Async callback receiving each :class:`TransferIntent` after it is signed and
            before it is sent. Save it to verify the transfer on-chain by ``msg_hash`` if the process dies
            before returning the purchase result. If it raises, that payment is not sent; the other payments of its
            group go out signed again, so a hook may be called again for the same ``req_id`` with a new ``msg_hash``.
        transfer_coordinator: Serializes signing and sending of the wallet's transfers and shares its pending
            seqno, per wallet address. Defaults to one that covers this process; pass a shared one (e.g.
            Redis-backed) when several processes buy from the same wallet.
        max_batch: Most payments sent to Fragment in one message of the wallet. Purchases that queue up while the
            previous message waits for its block go out together, one seqno and one provider call for all of them.
            Defaults to ``1``; the wallet caps it (W5 and Telegram Wallet 255, V4R2 4, highload 254 / 64516).

    Clients of one wallet in a process share its payment queue, and a group follows the settings of its first payment:
    give them the same ``max_batch`` and ``transfer_coordinator``.

    The client keeps one HTTP session and one blockchain API connection and reuses them across calls.
    Use ``async with`` (or call :meth:`aclose`) to release them when you are done.

    Purchases can run concurrently: only signing and sending the transfer is serialized (by the coordinator),
    the waiting for Fragment's confirmation is not. Payments queue per wallet within a process, so share one client
    (or a few) per process to let them group. Keep the system clock synced.

    Raises:
        ConfigurationError: If ``seed``, ``api_key``, ``wallet_version``, ``mnemonic_type``,
            ``api_provider``, ``confirm_timeout`` or ``max_batch`` are missing or invalid.
        CookieError: If ``cookies`` cannot be parsed or are missing required keys.

    Example::

        async with FragmentClient(
            seed="word1 word2 ...",
            api_key="AAABBB...",
            cookies={"stel_token": "...", "stel_ton_token": "..."},
        ) as client:
            print(await client.get_wallet())
            result = await client.purchase_premium("@username", months=6)
            print(result.transaction_id)
    """
