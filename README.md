易失的不可记忆密钥系统
========================

易失的不可记忆密钥（VNMK）系统，是一个服务器，
可以保管并（在经过严格验证的情况下）释出用户预先存入的密码，以便用户使用。

用户可以通过多种第三方服务向服务器证明自己的身份，还需要输入一个访问口令，
才可以获得事先托管的机密信息。

用户一旦访问服务器，就会启动一个具有倒计时限制的会话。
这一倒计时只会在用户成功登录、获取机密信息的情况下停止。
**如果用户没有在倒计时内成功登录，或者输入了错误的访问口令，服务器就会立刻销毁托管的信息。**
利用这种方式，本系统可以保管用户的一部分密钥，用来解密最重要的数据。

这样，即使用户失去自由、受到胁迫，无论是即时的暴力，还是持续的威胁，
都有办法让密钥消失，令胁迫者永远失去解密数据的机会。

服务器上的机密信息本身可以是经过对称加密（口令加密）的OpenPGP密文，
这样最终的解密在用户的浏览器上进行，即使服务器上的托管信息泄露，也不会暴露原文。

---

Volatile Non-Memorable Key System
=================================

The Volatile Non-Memorable Key(VNMK) system, is a server designed at storing
and (after strict identification) releasing user saved credential.

The user may authenticate itself via 3rd party ID providers. Together with an
access code, the credential will be released.

Once the user attempts accessing the server, a session with countdown will be
created.  This countdown will only reset after a success login, where
credential will be released.  **If the user failed logging in within countdown
time, or provided a wrong access code, the server will destroy stored data
immediately.**

In this way, even if the user loses its control and was forced to release the
credential, whether due to immediate violance or persisting threat, it will
have the chance to make the credential disappear forever, letting the
threatener never able to decrypt anything protected under this credential.

Credential stored at server can be OpenPGP encrypted(with a passphrase)
ciphertext, so that its decryption will be carried out at user's browser. Even
if there's a data leakage at server side, the really important part will be
kept secret.
