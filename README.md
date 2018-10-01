易失的不可记忆密钥系统
========================

易失的不可记忆密钥（VNMK）系统，是一个服务器，
可以保管并（在经过严格验证的情况下）释出用户预先存入的密码，以便用户使用。

用户可以通过多种第三方服务向服务器证明自己的身份，还需要输入一个访问口令，
才可以获得事先托管的机密信息。

## 这个服务器在设计上是一个不稳定的系统

它需要经常在两个状态（套用物理学名词，我们称之为**基态**和**激发态**）之间切换，
才可以保证用户托管的密钥不会被删除：

1. 无论进入基态还是激发态，进入的时候一开始，都会启动一个倒计时。
   * 基态的倒计时较长，默认为7天。
   * 激发态的倒计时较短，默认为1个小时。
2. 无论是基态还是激发态，倒计时一旦到零，都会导致用户托管的密钥被立刻销毁。
3. 两个状态之间可以相互转换：
   1. 用户访问服务器的行为，会把处于基态的服务器立刻转换为激发态。
      但如果服务器此时已经处于激发态，就不会发生变化。
   2. 用户能，且只能在一次成功的登录（凭此获得托管的数据）之后，
      才能将服务器转换回基态。
   3. 如果在激发态上，用户成功地证明了自己的身份，但是输入了错误的访问口令，
      则服务器将会立刻销毁托管的密钥。

## 这样设计的目的是什么？

本系统设计上用来保存用户的机密信息，比如磁盘的解密密码（的一部分），
避免其他人通过身体/心理/社会施压，强迫用户交出数据。

为了消除任何身心折磨的意义，这一数据必须**不能**被用户记在头脑中，
只能通过访问服务器的方式随用随取。
这样，用户或者任何人想要解密磁盘，就被迫访问一次本服务器。

因为想要获取解密信息，除了通过第三方身份认证外，还必须输入一个访问口令，
而这种尝试的机会只有一次、且必须在激发态的1个小时内完成，所以在面临强大的逼迫时，
用户有机会给出错误的口令，指令销毁密钥。这样，被密钥保护的磁盘就将永远无法解密。

即使胁迫者了解到上述规则，试图通过软磨硬泡等持续威胁的方式，
打算让用户交出正确的口令，但在得到口令之前，又不尝试访问服务器（以免将服务器激发），
这样的状况也是有期限的，因为基态下服务器同样有7天的倒计时，逾期密钥也会被销毁。


这样，即使用户失去自由、受到胁迫，无论是即时的暴力，还是持续的威胁，
都有办法让密钥消失，令胁迫者永远失去解密数据的机会。

服务器上的机密信息本身可以是经过对称加密（口令加密）的OpenPGP密文，
这样最终的解密在用户的浏览器上进行，即使服务器上的托管信息泄露，也不会暴露原文。

## 配置方法

要使用本系统，您需要一个单独的服务器（这个服务器上将存储加密过的数据主体），
以及一个Google帐号（用于使用Google的Firebase服务）。

### Firebase

访问 [https://console.firebase.google.com](https://console.firebase.google.com)
建立您的项目。请参考Google文档了解如何进行。

您需要为项目启用**身份验证**和**实时数据库**功能。

* 身份验证，可以配置启用Google登录和Github登录。
* 实时数据库中的规则，使用`firebase.rules.json`文件的内容。

此后您需要建立一个服务账号，并下载相应的密钥，用于独立服务器配置。

### 独立服务器

在独立服务器上，请在合适的位置利用`git clone`获得本项目的备份。

```
$ git clone https://github.com/neoatlantis-security-solutions/vnmk
$ cd vnmk
```

在`vnmk`目录中，您可以使用`python3 -m vnmk.server <配置文件.yaml>`
这样的方式来启动服务器。但为了初始化服务器的状态，还需要一些额外的工作。

#### 初始化服务器状态

首先您需要根据`config.example.zh.yaml`这个模板，建立自己的配置文件。
前文所述由Google获得的服务帐号密钥，需要按照模板格式写入文件。

然后，使用如下命令

```
$ python3 -m vnmk.server <配置文件.yaml> --init <机密信息文件>
```

初始化服务器。程序将加密机密信息，将之保存在配置文件中所指定的工作目录。
之后，加密密钥将上传至Firebase。

成功后，程序运行将会退出。之后运行，如前面所述去掉`--init <机密信息文件>`选项，
重新运行服务器，就可以通过所配置的地址访问了。




---

Volatile Non-Memorable Key System
=================================

The Volatile Non-Memorable Key(VNMK) system, is a server designed at storing
and (after strict identification) releasing user saved credential.

The user may authenticate itself via 3rd party ID providers. Together with an
access code, the credential will be released.

## It's an unstable system by design

In order to prevent the user stored credential from being destroyed, the system
must be frequently switched between two states(borrowing terminology from
physics, we call them **ground state** and **excited state**).

1. Both states have countdowns, starting when the server enters that state.
   * At ground state, the countdown is longer, by default 7 days.
   * At excited state, the countdown is short, by default 1 hour.
2. Whichever state the server is in, once the countdown reaches zero, user
   stored credential will be destroyed immediately.
3. The server may switch between both states.
   1. An access to the server, turns server into excited state from ground
      state. But if server was already excited, nothing will happen.
   2. The server will return to ground state, after, and only after the user
      have performed a successful login(by which it will retrieve stored
      credential).
   3. If the user identifies itself successfully but have entered a wrong
      access code, server will destroy stored credential immediately.
   
## What's the point for such design?

The system is designed to guard user's credential, such as part of the key used
for decrypting its hard disk, against any physical/psychologically/social
pressure/threat/tortures from outside.

To eliminate any sense with torture, this part of data **MUST NOT** be
remembered by user. Rather, it must be retrieved from server on the fly. In
such way anyone, including the user, is forced to access the server before
decrypting its disk.

To get this access, along with a 3rd party identification, the user must supply
an access code. There's only one attempt and must be completed within the 1
hour countdown within excited state. Therefore the user is given the chance,
under powerful threat to give out a wrong access code, commanding server
destroy the credential. After that, any disk encrypted by this credential will
be rendered undecryptable forever.

Even though a threatener is known of above rules and attempts to threat a user
continously, to get a certain correct access code before accessing the server
in real(thus avoid exciting the server), there's a time limit on that: as in
ground state another countdown of 7 days apply, after which credential will also
be destroyed.

In this way, even if the user loses its control and was forced to release the
credential, whether due to immediate violance or persisting threat, it will
have the chance to make the credential disappear forever, letting the
threatener never able to decrypt anything protected under this credential.

Credential stored at server can be OpenPGP encrypted(with a passphrase)
ciphertext, so that its decryption will be carried out at user's browser. Even
if there's a data leakage at server side, the really important part will be
kept secret.
